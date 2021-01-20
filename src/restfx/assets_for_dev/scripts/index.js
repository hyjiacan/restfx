function loadPage() {
  var apis = {}

  function serializeParams (params) {
    var temp = []
    for (var key in params) {
      temp.push(key + '=' + params[key])
    }
    return '?' + temp.join('&')
  }

  function request (method, url, options) {
    var xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        options.callback(getResponse(xhr))
      }
    }
    if (options.param) {
      url += serializeParams(options.param)
    }
    xhr.open(method.toUpperCase(), url, true)
    xhr.setRequestHeader('accept', 'application/json;text/*')
    xhr.setRequestHeader('requested-with', 'XmlHttpRequest')
    // var form = new FormData()
    // if (options.data) {
    //   for (key in options.data) {
    //     if (!key) {
    //       continue
    //     }
    //     form.append(key, options.data[key])
    //   }
    // }
    xhr.send(options.data)
  }

  /**
   *
   * @param {XMLHttpRequest} xhr
   * @returns {headers: {}, data: string}
   */
  function getResponse (xhr) {
    var data = xhr.responseText
    var headers = {}
    xhr
      .getAllResponseHeaders()
      .split('\r\n')
      .forEach(function(item) {
        var temp = item.trim().split(':')
        if (!temp[0]) {
          return
        }
        headers[temp[0].trim()] = (temp[1] || '').trim()
      })
    var contentType = headers['content-type']
    if (!contentType) {
      headers['content-type'] = contentType = ''
    }
    if (contentType.indexOf('application/json') !== -1) {
      try {
        data = JSON.parse(data)
      } catch (e) {
      }
    }
    return {
      data: data,
      headers: headers,
      status: xhr.status,
      statusText: xhr.statusText
    }
  }

  var list = document.querySelector('#api-list')
  var rootURL = window.location.protocol + '//' + window.location.host + window.location.pathname

  // 请求数据
  document.querySelector('#loading').style.display = 'block'
  request('post', rootURL, {
    callback: function(response) {
      if (response.status !== 200) {
        list.innerHTML = response.data
        return
      }
      var data = response.data
      render(typeof data === 'string' ? JSON.parse(data) : data)
    }
  })

  function render (data) {
    document.querySelector('#fx-name').innerHTML = data.meta.name + '@' + data.meta.version
    document.title = 'Table of APIs - ' + data.app_name
    document.querySelector('#app-name').innerHTML = data.app_name

    var apis = data.apis
    if (!apis || !Object.keys(apis).length) {
      document.querySelector('#loading').innerHTML = '未找到接口信息'
      return
    }



    var apiList = el('ol', {
      'class': 'api-items'
    })

    var modules = Object.keys(apis)
    modules.sort()
    modules.forEach(function(module){
      apiList.appendChild(el('li', {
        'class': 'module-item'
      }, renderModule(apis[module], module, data.expanded)))
    })

    list.innerHTML = ''
    list.appendChild(apiList)
  }

  function renderModule (data, module, expanded) {
    var encodedModuleName = module.split('').map(function(ch) {return ch.charCodeAt(0).toString(32)}).join('-')
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
        el('span', null, module)
      ]),
      el(
        'ol',
        { 'class': 'api-list' },
        data.map(function(route) {
            var id = route.method + '#' + route.path
            apis[id] = route
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
                el('span', { 'class': 'route-name' }, route.name),
                el('span', { 'class': 'comment' }, route.func_desc)
              ]),
              el('div', {
                'class': 'url-info'
              }, [
                el('div', { 'class': 'info' }, [
                  el('span', { 'class': 'method' }, route.method),
                  el('code', { 'class': 'url' }, [
                    el('span', {
                      'class': 'url-prefix'
                    }, rootURL),
                    el('span', {
                      'class': 'url-path'
                    }, route.path)
                  ])
                ]),
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

  function getArgDefaultValue (arg) {
    var defaultValue = arg['default']
    if (defaultValue === null) {
      return 'None'
    }

    if (defaultValue === '') {
      return '""'
    }

    if (typeof defaultValue === 'number') {
      return defaultValue.toString()
    }

    if (typeof defaultValue === 'boolean') {
      return defaultValue ? 'True' : 'False'
    }

    return defaultValue
  }

  function renderArgDefaultValue (arg) {
    if (!arg.has_default) {
      return el('span', null, '-')
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

    if (['bool', 'int', 'float'].indexOf(arg.annotation_name) === -1) {
      editor = el('textarea', attrs, arg.has_default ? arg['default'] : '')
    } else {
      attrs.value = arg.has_default ? arg['default'] : ''
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
        'class': 'arg-name'
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
          { 'class': 'comment' },
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

    var rows = args.map(function(arg){return renderArg(arg, editable)})

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

  //-----测试相关
  var testPanel = document.querySelector('#test-panel')
  document.querySelector('#btn-close-test').addEventListener('click', function () {
    testPanel.style.display = 'none'
  })
  document.querySelector('#btn-send-test').addEventListener('click', function () {
    var method = testPanel.querySelector('.method').textContent.trim()
    var url = testPanel.querySelector('.url').textContent.trim()
    testPanel.querySelector('div.response-content').innerHTML = ''
    testPanel.querySelector('textarea.response-content').value = ''
    testPanel.querySelector('div.response-content').style.display = 'none'
    testPanel.querySelector('textarea.response-content').style.display = 'none'
    testPanel.querySelector('.response-status').classList.remove('status-success', 'status-failed')
    testPanel.querySelector('.status-code').textContent = ''
    testPanel.querySelector('.status-text').textContent = ''
    testPanel.querySelector('.response-time').textContent = ''

    var fields = {}
    var temp = testPanel.querySelectorAll('input.arg-value')
    for (var index = 0; index < temp.length; index++) {
      var field = temp[index]
      if (field.required && !field.value) {
        field.classList.add('required')
        return
      }
      field.classList.remove('required')
      fields[field.name] = field.value
    }
    temp = testPanel.querySelectorAll('textarea.arg-value')
    for (var index = 0; index < temp.length; index++) {
      var field = temp[index]
      if (field.required && !field.value) {
        field.classList.add('required')
        return
      }
      field.classList.remove('required')
      fields[field.name] = field.value
    }
    testPanel.querySelector('.response-time').textContent = 'Loading...'
    var start = new Date().getTime()
    var option = {
      callback: function(response) {
        var end = new Date().getTime()
        testPanel.querySelector('.response-time').textContent = (end - start) + 'ms'
        renderTestResponse(response)
      }
    }

    if (['get', 'devare'].indexOf(method) === -1) {
      option.data = fields
    } else {
      option.param = fields
    }

    request(method, url, option)
  })
  document.body.addEventListener('click', function (e) {
    if (e.target.classList.contains('btn-open-test')) {
      openTestPanel(e)
    }
  })

  function openTestPanel (e) {
    var id = e.target.getAttribute('data-api')
    var api = apis[id]
    testPanel.querySelector('.module').textContent = api.module
    testPanel.querySelector('.name').textContent = api.name
    testPanel.querySelector('.method').textContent = api.method
    testPanel.querySelector('.url').textContent = rootURL + api.path

    if(api.addition_info){
      testPanel.querySelector('.addition-info').innerHTML = api.addition_info
      testPanel.querySelector('.addition-info').style.display = 'block'
    } else {
      testPanel.querySelector('.addition-info').style.display = 'none'
    }

    var table = testPanel.querySelector('table')
    var tableContainer = table.parentElement

    tableContainer.replaceChild(renderArgs(api.handler_info.arguments, true), table)

    testPanel.querySelector('.status-code').textContent = ''
    testPanel.querySelector('.status-text').textContent = ''
    testPanel.querySelector('div.response-content').innerHTML = ''
    testPanel.querySelector('textarea.response-content').value = ''
    testPanel.querySelector('div.response-content').style.display = 'none'
    testPanel.querySelector('textarea.response-content').style.display = 'none'
    testPanel.querySelector('.response-time').textContent = ''

    testPanel.style.display = 'flex'
  }

  function renderTestResponse (response) {
    var classList = testPanel.querySelector('.response-status').classList
    classList.remove('status-success', 'status-failed')
    classList.add(response.status === 200 ? 'status-success' : 'status-failed')
    testPanel.querySelector('.status-code').textContent = response.status
    testPanel.querySelector('.status-text').textContent = response.statusText

    if (response.headers['content-type'].indexOf('text/html') !== -1) {
      testPanel.querySelector('div.response-content').innerHTML = response.data
      testPanel.querySelector('div.response-content').style.display = 'block'
      return
    }

    var content

    try {
      if (typeof response.data === 'string') {
        content = response.data
      } else {
        content = JSON.stringify(response.data, null, 4)
      }
    } catch (e) {
      content = response.data
    }

    testPanel.querySelector('textarea.response-content').value = content
    testPanel.querySelector('textarea.response-content').style.display = 'block'
  }

  document.querySelector('#btn-fullscreen').addEventListener('click', function() {
    if (testPanel.classList.contains('fullscreen')) {
      testPanel.classList.remove('fullscreen')
    } else {
      testPanel.classList.add('fullscreen')
    }
  })

  document.querySelector('#tools').style.display = 'block'
}

var all

function getAll () {
  if (all) {
    return all
  }
  all = document.body.querySelectorAll('details')
  return all
}

function collapseAll () {
  getAll().forEach(function (item) {
    item.removeAttribute('open')
  })
}

function expandAll () {
  getAll().forEach(function (item) {
    item.setAttribute('open', '')
  })
}

(function() {
  if (!!window.ActiveXObject || "ActiveXObject" in window) {
    var matchIE = /^.+?MSIE\s(.+?);.+?Trident.+$/.exec(window.navigator.userAgent)

    // IE11 没有 MSIE 串
    var ieVersion = matchIE ? parseFloat(matchIE[1]) : 11

    var tip = document.getElementById('ie-tip')
    tip.onclick = function() {
      // 2021.01.20
      // [
      //   '　　　　　IE之苦　　　　　　',
      //   '',
      //   '未知何缘何故，仍为 IE 服务。',
      //   '回看谷歌火狐，似乎形同陌路。',
      //   '却说如今微软，踏上EDGE新途。',
      //   '不与 IE 为伍，不受 IE 束缚。',
      //   '遵从前端标准，管他领导客户。',
      //   '愿君脱离苦海，独自潇洒如故。',
      //   '',
      //   '　　　　　　-- 开发者 hyjiacan'
      // ].join('\n')
      alert('\u3000\u3000\u3000\u3000\u3000\u0049\u0045\u4e4b\u82e6\u3000\u3000\u3000\u3000\u3000\u3000\u000d\u000a\u000d\u000a\u672a\u77e5\u4f55\u7f18\u4f55\u6545\uff0c\u4ecd\u4e3a\u0020\u0049\u0045\u0020\u670d\u52a1\u3002\u000d\u000a\u56de\u770b\u8c37\u6b4c\u706b\u72d0\uff0c\u4f3c\u4e4e\u5f62\u540c\u964c\u8def\u3002\u000d\u000a\u5374\u8bf4\u5982\u4eca\u5fae\u8f6f\uff0c\u8e0f\u4e0a\u0045\u0044\u0047\u0045\u65b0\u9014\u3002\u000d\u000a\u4e0d\u4e0e\u0020\u0049\u0045\u0020\u4e3a\u4f0d\uff0c\u4e0d\u53d7\u0020\u0049\u0045\u0020\u675f\u7f1a\u3002\u000d\u000a\u9075\u4ece\u524d\u7aef\u6807\u51c6\uff0c\u7ba1\u4ed6\u9886\u5bfc\u5ba2\u6237\u3002\u000d\u000a\u613f\u541b\u8131\u79bb\u82e6\u6d77\uff0c\u72ec\u81ea\u6f47\u6d12\u5982\u6545\u3002\u000d\u000a\u000d\u000a\u3000\u3000\u3000\u3000\u3000\u3000\u002d\u002d\u0020\u5f00\u53d1\u8005\u0020\u0068\u0079\u006a\u0069\u0061\u0063\u0061\u006e')
    }
    if (ieVersion < 10) {
      // 恶心提示: 此页面不支持 <b>IE9及更低版本的IE浏览器</b>，请更换浏览器以获得更好的使用体验！
      tip.innerHTML = '\u6076\u5fc3\u63d0\u793a\u003a\u0020\u6b64\u9875\u9762\u4e0d\u652f\u6301\u0020' +
       '<b>' + '\u0049\u0045\u0039\u53ca\u66f4\u4f4e\u7248\u672c\u7684\u0049\u0045\u6d4f\u89c8\u5668' + '</b>' +
       '\uff0c\u8bf7\u66f4\u6362\u6d4f\u89c8\u5668\u4ee5\u83b7\u5f97\u66f4\u597d\u7684\u4f7f\u7528\u4f53\u9a8c\uff01'
      tip.style.display = 'block'
      return
    }
    // 恶心提示: 此页面对 <b>IE浏览器</b> 不友好，请更换浏览器以获得更好的使用体验！
    tip.innerHTML = '\u6076\u5fc3\u63d0\u793a\u003a\u0020\u6b64\u9875\u9762\u5bf9\u0020' +
      '<b>' + '\u0049\u0045\u6d4f\u89c8\u5668' + '</b>' +
      '\u0020\u4e0d\u53cb\u597d\uff0c\u8bf7\u66f4\u6362\u6d4f\u89c8\u5668\u4ee5\u83b7\u5f97\u66f4\u597d\u7684\u4f7f\u7528\u4f53\u9a8c\uff01'
    tip.style.display = 'block'
  }

  loadPage()
})();