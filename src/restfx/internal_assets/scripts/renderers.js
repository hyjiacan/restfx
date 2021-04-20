function el(tag, attrs, children) {
  var element = document.createElement(tag)
  var isHTML = false
  if (attrs) {
    for (var name in attrs) {
      var val = attrs[name]
      if (val === undefined) {
        continue
      }
      if (name === 'html') {
        isHTML = !!val
        continue
      }
      element.setAttribute(name, val)
    }
  }
  if (isHTML) {
    element.innerHTML = children
    return element
  }

  if (children) {
    if (!Array.isArray(children)) {
      children = [children]
    }
    children.forEach(function (child) {
      if (child === undefined || child === null) {
        return
      }
      if (!(child instanceof Node)) {
        child = document.createTextNode(child.toString())
      }
      element.appendChild(child)
    })
  }
  return element
}

function formatComment(comment) {
  if (Object.prototype.toString.call(comment) !== '[object Array]') {
    return comment
  }
  return comment.map(function (item) {
    if (item.type === 'code') {
      return '<pre><code>' + item.lines.join('') + '</code></pre>'
    }
    if (!$.trim(item.lines[0])) {
      item.lines.shift()
    }
    return item.lines.map(function (line) {
      return line.replace(/\t/g, '    ')
        .replace(/ /g, '&nbsp;')
        .replace(/`(.+?)`/g, function (match, code) {
          return '<code>' + code + '</code>'
        })
    }).join('').replace(/\n/g, '<br/>')
  }).join('')
}

function render(list, data) {
  document.title = 'Table of APIs - ' + data.name
  $('#app-name').html(data.name)

  var poweredLink = $('#fx-name')
  poweredLink.html(data.meta.name + '@' + data.meta.version)
  poweredLink.attr('href', data.meta.url + '?from=dist&version=' + data.meta.version)
  var s = localStorage.getItem('options-expanded')
  if (s !== undefined && s !== null && s !== '') {
    data.expanded = s === '1'
  }
  $('#expanded-on-load').prop('checked', data.expanded)

  var routes = data.routes
  if (!routes || !routes.length) {
    $('#loading').html('未找到接口信息')
    return
  }

  var apiList = el('ol', {
    'class': 'api-items'
  })

  var modules = Object.create(null)
  var moduleNames = []
  for (var i = 0; i < routes.length; i++) {
    var route = routes[i]
    // if (!route.module) {
    //   route.module = '<未命名模块>'
    // }
    // if (!route.name) {
    //   route.name = '<未命名路由>'
    // }
    if (!modules[route.module]) {
      modules[route.module] = []
      moduleNames.push(route.module)
    }
    modules[route.module].push(route)
  }

  moduleNames.sort()
  moduleNames.forEach(function (moduleName) {
    apiList.appendChild(el('li', {
      'class': 'module-item'
    }, renderModule(modules[moduleName], moduleName, data.expanded)))
  })

  window.apiData = {
    name: data.name,
    meta: data.meta,
    moduleNames: moduleNames,
    modules: modules
  }

  list.empty().append(apiList)

  $('#api-summary .count1').text(moduleNames.length)
  $('#api-summary .count2').text(routes.length)

  // 滚动到指定项
  goToAnchor()
}

function goToAnchor() {
  // substr(1) 用于移除前导的 # 符号
  var hash = window.location.hash.substr(1)
  if (!hash) {
    return
  }
  var anchors = $('a[name].anchor')
  for (var i = 0; i < anchors.length; i++) {
    var anchor = anchors.eq(i)
    if (anchor.attr('name') !== hash) {
      continue
    }
    if (anchor.parent().is('summary')) {
      // 锚点是模块，那么直接滚动到其位置
      anchor.get(0).scrollIntoView()
      break
    }
    // 锚点是路由，那么展开其所在模块，然后滚动到其位置
    // dom 路径是固定的，所以使用 4 个 parent() 就能找到模块元素
    var module = anchor.parent().parent().parent().parent()
    module.prop('open', 'open')
    // -60 用于修正 模块名称使用了 sticky 定位时占用的高度
    var offsetTop = anchor.get(0).offsetTop - 60
    $('#app').scrollTop(offsetTop)
    break
  }
}

function renderModule(routes, moduleName, expanded) {
  routes.sort(function (item1, item2) {
    return item1.path > item2.path ? 1 : -1
  })
  var encodedModuleName = encodeURI(moduleName)
  return el('details', {
    open: expanded ? 'open' : undefined
  }, [
    el('summary', null, [
      el(
        'a',
        {
          href: '#' + encodedModuleName,
          name: encodedModuleName,
          'class': 'anchor',
          html: true
        },
        '&sect;'
      ),
      el('span', {
        'class': 'module-name' + (moduleName ? '' : ' unnamed-item')
      }, moduleName || '<未命名>'),
      el('span', {
        'class': 'route-count',
        title: '此模块中包含的路由数量'
      }, '*' + routes.length)
    ]),
    el(
      'ol',
      {'class': 'api-list'},
      routes.map(function (route) {
          var id = route.method + '#' + route.path
          API_LIST[id] = route
          var encodedRoutePath = encodeURI(route.method + ':' + route.path)
          return el('li', {'class': 'api-item'}, [
            el('div', null, [
              el(
                'a',
                {
                  href: '#' + encodedRoutePath,
                  name: encodedRoutePath,
                  'class': 'anchor',
                  html: true
                },
                '&sect;'
              ),
              el('span', {
                'class': 'route-name' + (route.name ? '' : ' unnamed-item')
              }, route.name || '<未命名>')
            ]),
            route.handler_info.description ?
              el('p', {'class': 'comment route-description', html: true},
                formatComment(route.handler_info.description)
              ) : '',
            el('div', {
              'class': 'url-info'
            }, [
              renderUrlInfo(route),
              el('button', {
                'class': 'btn-open-test',
                'data-api': id
              }, '测试')
            ]),
            route.addition_info ? el('div', {
              'class': 'addition-info',
              html: true
            }, route.addition_info) : null,
            renderArgs(route.handler_info.arguments),
            renderReturn(route)
          ])
        }
      )
    )
  ])
}

function renderUrlInfo(route) {
  return el('div', {'class': 'info'}, [
    el('span', {'class': 'method select-all'}, route.method),
    el('code', {'class': 'url'}, [
      el('span', {
        'class': 'url-root'
      }, urlRoot),
      el('span', {'class': 'url-prefix-with-slash'}, [
        el('span', null, '/'),
        el('span', {
          'class': 'url-prefix'
        }, [
          el('span', null, apiPrefix),
          el('span', {
            'class': 'url-path-with-slash'
          }, [
            el('span', null, '/'),
            el('span', {
              'class': 'url-path'
            }, route.path.substring(1))
          ])
        ])
      ])
    ])
  ])
}

function getArgValueString(value, editable) {
  if (value === null || value === undefined) {
    return editable ? '' : 'null'
  }

  if (typeof value === 'number') {
    return value.toString()
  }

  if (typeof value === 'boolean') {
    return value ? 'true' : 'false'
  }

  if (!editable && typeof value === 'string') {
    return '"' + value + '"'
  }

  return value
}

function getArgDefaultValue(arg, editable) {
  var defaultValue = arg['default']

  // 将元组和列表视作同种类型
  // 事实上，后台已经处理过这个类型，此处并不会接收到 tuple 类型
  if (arg.annotation_name !== 'list' || defaultValue === null) {
    return getArgValueString(defaultValue, editable)
  }

  var listValue = defaultValue.map(function (item) {
    return getArgValueString(item, editable)
  }).join(',')

  // 使用 逗号 分隔开
  return '[' + listValue + ']'
}

function renderArgDefaultValue(arg) {
  if (!arg.has_default) {
    return el('span', {
      'class': 'required-field',
      title: '必填项'
    }, '*')
  }
  return el('code', null, getArgDefaultValue(arg))
}

function renderArgEditor(arg) {
  var attrs = {
    type: 'text',
    name: arg.name,
    'class': 'arg-value',
    'data-type': arg.annotation_name
  }
  if (!arg.has_default) {
    attrs.required = 'required'
  }

  var editor
  if (arg.annotation_name === 'HttpFile') {
    attrs.type = 'file'
    editor = el('input', attrs)
  } else if (['bool', 'int', 'float'].indexOf(arg.annotation_name) === -1) {
    editor = el('textarea', attrs, arg.has_default ? getArgDefaultValue(arg, true) : '')
  } else {
    attrs.value = arg.has_default ? getArgDefaultValue(arg, true) : ''
    editor = el('input', attrs)
  }

  return el('div', {'class': 'arg-editor'}, editor)
}

function renderArg(arg, editable) {
  var argName = arg.name
  if (arg.alias) {
    argName += '/' + arg.alias
  }
  var argType
  if (arg.is_variable) {
    arg.has_annotation = true
    argName = '**' + argName
    argType = 'variable'
  } else if (arg.has_annotation) {
    argType = arg.annotation_name
    if (argType === 'str') {
      argType = 'string'
    } else if (argType === 'HttpFile') {
      argType = 'file'
    } else if (argType === 'list') {
      argType = 'array'
    }
  } else {
    argType = '-'
  }

  return el('tr', null, [
    el('td', null, el('span', {
      'class': 'arg-name select-all'
    }, argName)),
    el(
      'td',
      null,
      el(
        arg.has_annotation ? 'code' : 'span',
        {
          'class': 'arg-type' + (arg.is_variable ? ' is-variable' : '')
        },
        argType
      )
    ),
    el(
      'td',
      null,
      editable && !arg.is_variable ? renderArgEditor(arg) : renderArgDefaultValue(arg)
    ),
    el(
      'td',
      null,
      el(
        'span',
        {'class': 'comment', html: true},
        formatComment(arg.comment || '-')
      )
    )
  ])
}

function renderArgs(args, editable, append) {
  if (!args || !args.length) {
    return el('table', {'class': 'args-table'}, [
      el('tr', null, el('td', null, [
        el('span', null, '参数信息: '),
        el('span', {'class': 'tip'}, '无')
      ]))
    ])
  }

  var rows = args.filter(function (arg) {
    // 编辑时不渲染 可变参数
    return !editable || !arg.is_variable
  }).map(function (arg) {
    return renderArg(arg, editable)
  })

  if (append) {
    rows.push(append)
  }

  return el('table', {'class': 'args-table'}, [
    el('colgroup', null, [
      el('col', {style: 'width: 200px'}, null),
      el('col', {style: 'width: 150px'}, null),
      el('col', {style: 'width: 200px'}, null),
      el('col', {style: 'width: auto'}, null)
    ]),
    el(
      'thead',
      null,
      el('tr', null, [
        el('th', null, '参数名称/别名'),
        el('th', null, '参数类型'),
        el('th', null, editable ? '值' : '默认值'),
        el('th', null, '描述')
      ])
    ),
    el(
      'tbody',
      null,
      rows
    )
  ])
}

function renderReturn(route) {
  return el('p', {'class': 'return-info'}, [
    el('span', null, '返回'),
    // route.handler_info.return_type ? el('code', null, route.return_type) : '',
    el('span', null, ': '),
    el('span', {'class': 'comment', html: true},
      formatComment(route.handler_info.return_description || '-')
    )
  ])
}
