function el (tag, attrs, children) {
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
    children.forEach(function(child) {
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
function render (list, data) {
  document.querySelector('#fx-name').innerHTML = data.meta.name + '@' + data.meta.version
  document.title = 'Table of API_LIST - ' + data.app_name
  document.querySelector('#app-name').innerHTML = data.app_name
  var s = localStorage.getItem('options-expanded')
  if (s !== undefined) {
    data.expanded = s === '1'
  }
  document.querySelector('#expanded-on-load').checked = data.expanded

  var routes = data.routes
  if (!routes || !routes.length) {
    document.querySelector('#loading').innerHTML = '未找到接口信息'
    return
  }

  var apiList = el('ol', {
    'class': 'api-items'
  })

  var modules = Object.create(null)
  var moduleNames = []
  for (var i = 0; i < routes.length; i++) {
    var route = routes[i];
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
  moduleNames.forEach(function(moduleName){
    apiList.appendChild(el('li', {
      'class': 'module-item'
    }, renderModule(modules[moduleName], moduleName, data.expanded)))
  })

  list.innerHTML = ''
  list.appendChild(apiList)
}

function padStart(str, width, fill) {
  for (var i=str.length;i<width;i++) {
    str = fill + str;
  }
  return str
}

function renderModule (data, moduleName, expanded) {
  var encodedModuleName = moduleName ? moduleName.split('').map(function(ch) {
    return padStart(ch.charCodeAt(0).toString(32), 4, '0')
  }).join('') : '00000000000000000000000000000000'
  return el('details',  {
    open: expanded ? 'open' : undefined
  }, [
    el('summary',null , [
      el(
        'a',
        {
          href: '#' + encodedModuleName,
          name: encodedModuleName,
          'class': 'anchor'
        },
        '#'
      ),
      el('span', {
        'class': moduleName ? '' : 'unnamed-item'
      }, moduleName || '<未命名>')
    ]),
    el(
      'ol',
      { 'class': 'api-list' },
      data.map(function(route) {
          var id = route.method + '#' + route.path
          API_LIST[id] = route
          return el('li', { 'class': 'api-item' }, [
            el('div', null, [
              el(
                'a',
                {
                  href: '#' + encodeURI(route.path),
                  name: encodeURI(route.path),
                  'class': 'anchor'
                },
                '#'
              ),
              el('span', {
                'class': 'route-name' + (route.name ? '' : ' unnamed-item')
               }, route.name || '<未命名>'),
              el('span', { 'class': 'comment', html: true }, route.handler_info.description)
            ]),
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
  return el('div', { 'class': 'info' }, [
    el('span', { 'class': 'method select-all' }, route.method),
    el('code', { 'class': 'url' }, [
      el('span', {
        'class': 'url-root'
      }, urlRoot),
      el('span', {'class': 'url-prefix-with-slash'}, [
        el('span', null, '/'),
        el('span', {
          'class': 'url-prefix'
        },  [
          el('span', null, apiPrefix),
          el('span', {
            'class': 'url-path-with-slash'
          }, [
            el('span', null, '/'),
            el('span', {
              'class': 'url-path'
            }, route.path.substring(1)),
          ])
        ])
      ])
    ])
  ])
}

function getArgValueString(value, editable) {
  if (value === null || value === undefined) {
    return editable ? '' : 'None'
  }

  if (typeof value === 'number') {
    return value.toString()
  }

  if (typeof value === 'boolean') {
    if (editable) {
      return value ? 'true' : 'false'
    }
    return value ? 'True' : 'False'
  }

  if (typeof value === 'string') {
    return '"' + value + '"'
  }

  return value
}

function getArgDefaultValue (arg, editable) {
  var defaultValue = arg['default']

  // 将元组和列表视作同种类型
  // 事实上，后台已经处理过这个类型，此处并不会接收到 tuple 类型
  if (arg.annotation_name !== 'list') {
    return getArgValueString(defaultValue, editable)
  }

  var listValue = defaultValue.map(function(item) {
    return getArgValueString(item, editable)
  }).join(',')

  // 使用 逗号 分隔开
  return '[' + listValue + ']'
}

function renderArgDefaultValue (arg) {
  if (!arg.has_default) {
    return arg.annotation_name === 'HttpRequest' ? el('span', null , '-') : el('span', {
      'class': 'required-field',
      title: '必填项'
    }, '*')
  }
  return el('code', null, getArgDefaultValue(arg))
}

function renderArgEditor (arg) {
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
  } else  {
    attrs.value = arg.has_default ? getArgDefaultValue(arg, true) : ''
    editor = el('input', attrs)
  }

  return el('div', { 'class': 'arg-editor' }, editor)
}

function renderArg (arg, editable) {
  var argName = arg.name
  if (arg.alias) {
    argName += '/' + arg.alias
  }
  var argType
  if (arg.is_variable) {
    arg.has_annotation = true
    argName = '**' + argName
    argType = 'VAR_KEYWORD'
  } else if (arg.has_annotation) {
    argType = arg.annotation_name
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
        null,
        argType
      )
    ),
    el(
      'td',
      null,
      editable && arg.annotation_name !== 'HttpRequest' && !arg.is_variable ?
        renderArgEditor(arg) : renderArgDefaultValue(arg)
    ),
    el(
      'td',
      null,
      el(
        'span',
        { 'class': 'comment', html: true},
        arg.comment ? arg.comment : '-'
      )
    )
  ])
}

function renderArgs (args, editable, append) {
  if (!args || !args.length) {
    return el('table', { 'class': 'args-table' }, [
      el('tr', null, el('td', null, [
        el('span', null, '参数信息: '),
        el('span', { 'class': 'tip' }, '无')
      ]))
    ])
  }

  var rows = args.filter(function(arg) {
    // 编辑时不渲染 可变参数
    if (editable && arg.is_variable) {
      return false
    }
    // 始终不显示 HttpRequest 参数 和 注入参数
    return arg.annotation_name !== 'HttpRequest' && !arg.is_injected
  }).map(function(arg){return renderArg(arg, editable)})

  if (append) {
    rows.push(append)
  }

  return el('table', { 'class': 'args-table' }, [
    el('caption', null, '参数信息'),
    el('colgroup', null, [
      el('col', { style: 'width: 200px' }, null),
      el('col', { style: 'width: 150px' }, null),
      el('col', { style: 'width: 200px' }, null),
      el('col', { style: 'width: auto' }, null)
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

function renderReturn (route) {
  return el('p', { 'class': 'return-info' }, [
    el('span', null, '返回'),
    // route.handler_info.return_type ? el('code', null, route.return_type) : '',
    el('span', null, ':'),
    el('span', { 'class': 'comment' }, route.handler_info.return_description || '-')
  ])
}
