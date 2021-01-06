;(function () {
  const apis = {}

  function serializeParams (params) {
    const temp = []
    for (const key in params) {
      temp.push(`${key}=${params[key]}`)
    }
    return '?' + temp.join('&')
  }

  function request (method, url, {
    param,
    data,
    headers,
    callback
  }) {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        callback(getResponse(xhr))
      }
    }
    if (param) {
      url += serializeParams(param)
    }
    xhr.open(method.toUpperCase(), url, true)
    xhr.setRequestHeader('requested-with', 'XmlHttpRequest')
    const form = new FormData()
    if (data) {
      for (key in data) {
        if (!key) {
          continue
        }
        form.append(key, data[key])
      }
    }
    xhr.send(form)
  }

  /**
   *
   * @param {XMLHttpRequest} xhr
   * @returns {headers: {}, data: string}
   */
  function getResponse (xhr) {
    let data = xhr.responseText
    let headers = {}
    xhr
      .getAllResponseHeaders()
      .split('\r\n')
      .forEach((item) => {
        let temp = item.trim().split(':')
        if (!temp[0]) {
          return
        }
        headers[temp[0].trim()] = (temp[1] || '').trim()
      })
    let contentType = headers['content-type']
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
      data,
      headers,
      status: xhr.status,
      statusText: xhr.statusText
    }
  }

  const list = document.querySelector('#api-list')
  const rootURL = window.location.origin + window.location.pathname
  // 请求数据
  request('post', rootURL, {
    callback: (response) => {
      if (response.status !== 200) {
        list.innerHTML = response.data
        return
      }
      render(response.data)
    }
  })

  function render (data) {
    if (!data || !Object.keys(data).length) {
      document.querySelector('#loading').innerHTML = '未找到接口信息'
      return
    }

    const fragment = document.createDocumentFragment()

    const modules = Object.keys(data)
    modules.sort()
    for (const module of modules) {
      fragment.appendChild(renderModule(data[module], module))
    }

    list.innerHTML = ''
    list.appendChild(fragment)
  }

  function renderModule (data, module) {
    let index = 0
    return el('details', { open: true }, [
      el('summary', null, [
        el(
          'a',
          {
            href: `#${module}`,
            name: module,
            class: 'anchor'
          },
          '#'
        ),
        el('span', null, module)
      ]),
      el(
        'ul',
        { class: 'api-list' },
        data.map((route) => {
            const id = route.method + '#' + route.path
            apis[id] = route
            return el('li', { class: 'api-item' }, [
              el('div', null, [
                el(
                  'a',
                  {
                    href: `#${route.path}`,
                    name: route.path,
                    class: 'anchor'
                  },
                  '#'
                ),
                el('span', { class: 'route-name' }, route.name),
                el('span', { class: 'comment' }, route.func_desc)
              ]),
              el('div', {
                class: 'url-info'
              }, [
                el('div', { class: 'info' }, [
                  el('span', { class: 'method' }, route.method),
                  el('code', { class: 'url' }, `${rootURL}${route.path}`)
                ]),
                el('button', {
                  class: 'btn-open-test',
                  'data-api': id
                }, '测试')
              ]),
              route.addition_info ? el('div', {
                class: 'addition-info',
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
    const defaultValue = arg['default']
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
    const attrs = {
      type: 'text',
      name: arg.name,
      class: 'arg-value',
      'data-type': arg.annotation_name
    }
    if (!arg.has_default) {
      attrs.required = 'required'
    }

    let editor

    if (['bool', 'int', 'float'].indexOf(arg.annotation_name) === -1) {
      editor = el('textarea', attrs, arg.has_default ? arg['default'] : '')
    } else {
      attrs.value = arg.has_default ? arg['default'] : ''
      editor = el('input', attrs)
    }

    return el('div', { class: 'arg-editor' }, editor)
  }

  function renderArg (arg, editable) {
    let argName = arg.name
    if (arg.alias) {
      argName += '/' + arg.alias
    }
    let argType
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
      el('td', null, argName),
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
          { class: 'comment' },
          arg.comment ? arg.comment : '-'
        )
      )
    ])
  }

  function renderArgs (args, editable, append) {
    if (!args) {
      return el('span', { class: 'tip' }, '无参数')
    }

    const rows = args.map(arg => renderArg(arg, editable))

    if (append) {
      rows.push(append)
    }

    return el('table', { class: 'args-table' }, [
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
    return el('p', { class: 'return-info' }, [
      el('span', null, '返回'),
      // route.handler_info.return_type ? el('code', null, route.return_type) : '',
      el('span', null, ':'),
      el('span', { class: 'comment' }, route.handler_info.return_description || '-')
    ])
  }

  function el (tag, attrs, children) {
    const element = document.createElement(tag)
    let isHTML = false
    if (attrs) {
      for (const name in attrs) {
        let val = attrs[name]
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
      children.forEach((child) => {
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
    const method = testPanel.querySelector('.method').textContent.trim()
    const url = testPanel.querySelector('.url').textContent.trim()
    testPanel.querySelector('div.response-content').innerHTML = ''
    testPanel.querySelector('textarea.response-content').value = ''
    testPanel.querySelector('div.response-content').style.display = 'none'
    testPanel.querySelector('textarea.response-content').style.display = 'none'
    testPanel.querySelector('.response-status').classList.remove('status-success', 'status-failed')
    testPanel.querySelector('.status-code').textContent = ''
    testPanel.querySelector('.status-text').textContent = ''
    testPanel.querySelector('.response-time').textContent = ''

    const fields = {}
    for (const field of testPanel.querySelectorAll('input.arg-value')) {
      if (field.required && !field.value) {
        field.classList.add('required')
        return
      }
      field.classList.remove('required')
      fields[field.name] = field.value
    }
    for (const field of testPanel.querySelectorAll('textarea.arg-value')) {
      if (field.required && !field.value) {
        field.classList.add('required')
        return
      }
      field.classList.remove('required')
      fields[field.name] = field.value
    }
    testPanel.querySelector('.response-time').textContent = 'Loading...'
    const start = new Date().getTime()
    const option = {
      callback: function(response) {
        const end = new Date().getTime()
        testPanel.querySelector('.response-time').textContent = (end - start) + 'ms'
        renderTestResponse(response)
      }
    }

    if (['get', 'delete'].indexOf(method) === -1) {
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
    const id = e.target.getAttribute('data-api')
    const api = apis[id]
    testPanel.querySelector('.module').textContent = api.module
    testPanel.querySelector('.name').textContent = api.name
    testPanel.querySelector('.method').textContent = api.method
    testPanel.querySelector('.url').textContent = `${rootURL}${api.path}`

    if(api.addition_info){
      testPanel.querySelector('.addition-info').innerHTML = api.addition_info
      testPanel.querySelector('.addition-info').style.display = 'block'
    } else {
      testPanel.querySelector('.addition-info').style.display = 'none'
    }

    let table = testPanel.querySelector('table')
    const tableContainer = table.parentElement

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
    const classList = testPanel.querySelector('.response-status').classList
    classList.remove('status-success', 'status-failed')
    classList.add(response.status === 200 ? 'status-success' : 'status-failed')
    testPanel.querySelector('.status-code').textContent = response.status
    testPanel.querySelector('.status-text').textContent = response.statusText

    if (response.headers['content-type'].indexOf('text/html') !== -1) {
      testPanel.querySelector('div.response-content').innerHTML = response.data
      testPanel.querySelector('div.response-content').style.display = 'block'
      return
    }

    let content

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
})()

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
