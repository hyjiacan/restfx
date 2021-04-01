(function () {
  var responseContent = $('div.response-content', testPanel)
  var responseStatus = $('.response-status', testPanel)
  var statusCode = $('.status-code', testPanel)
  var statusText = $('.status-text', testPanel)
  var responseTime = $('.response-time', testPanel)
  var responseLength = $('.response-length', testPanel)
  var responseType = $('.response-type', testPanel)

  function renderResponseInfo(xhr, start) {

    var end = new Date().getTime()
    responseTime.text('耗时: ' + (end - start) + 'ms')

    responseStatus.removeClass('status-success status-failure')
    responseStatus.addClass(xhr.status === 200 ? 'status-success' : 'status-failure')

    if (xhr.status === 0) {
        return
    }

    statusCode.text(xhr.status)
    statusText.text(xhr.statusText)

    var type = xhr.headers['content-type'].split(';')[0]
    responseType.text('Content-Type: ' + type)

    var len = ((xhr.headers['content-length'] / 1024).toFixed(2) * 100) / 100
    responseLength.text('Content-Length: ' + xhr.headers['content-length'] + ' (' + len + 'KB)')
  }

  function sendTest(method, url) {
    responseContent.empty().hide()
    responseStatus.removeClass('status-success status-failure')
    statusCode.empty()
    statusText.empty()
    responseTime.empty()
    responseLength.empty()

    var fields = Object.create(null)
    $('input.arg-value, textarea.arg-value', testPanel).each(function () {
      var field = $(this)
      field.removeClass('required')
      field = field[0]
      if (field.type === 'file') {
        fields[field.name] = {
          value: field.files[0]
        }
      } else {
        fields[field.name] = {
          value: field.value
        }
      }
      fields[field.name].type = field.dataset.type
    })
    responseTime.text('加载中...')

    var start = new Date().getTime()
    var option = {
      callback: function (response) {
        renderResponseInfo(response, start)

        if (response.status === 0) {
            return
        }
        renderTestResponse(response, url)
      }
    }
    // 处理数据格式
    var formData = Object.create(null)
    for (var name in fields) {
      // 忽略空的字段
      if (!name || /^\s*$/.test(name)) {
        continue
      }

      // var fieldType = fields[name].type

      var fieldValue = fields[name].value

      formData[name] = fieldValue
    }

    if (['get', 'delete'].indexOf(method) === -1) {
      option.data = new FormData()
      for (var name in formData) {
        option.data.append(name, formData[name])
      }
    } else {
      option.param = formData
    }

    xhr(method, url, option)
  }

  function addTestField(toolRow, allowForm) {
    var rowParent = toolRow.parentElement

    var nameField = el('input', {placeholder: '填写字段名称', 'class': 'arg-name'})

    var types = [
      el('option', {value: 'str'}, '字符串')
    ]

    // 是否允许表单，部分数据类型只有在允许表单时才能传输
    if (allowForm) {
      types = types.concat([
        el('option', {value: 'int'}, '整数'),
        el('option', {value: 'float'}, '小数'),
        el('option', {value: 'bool'}, '布尔值'),
        el('option', {value: 'list'}, '数组'),
        el('option', {value: 'HttpFile'}, '文件')
      ])
    }

    var typeField = el('select', {'class': 'arg-type'}, types)

    var valueField = el('input', {
      type: 'text',
      'data-type': 'str',
      'class': 'arg-value'
    })

    var removeButton = el('a', {
      href: 'javascript:',
      'class': 'btn-remove-test-field'
    }, '移除')

    var newRow = el('tr', {
      'class': 'test-row--tool'
    }, [
      el('td', null, nameField),
      el('td', null, typeField),
      el('td', null, valueField),
      el('td', null, removeButton)
    ])

    rowParent.insertBefore(newRow, toolRow)

    nameField.addEventListener('input', function () {
      valueField.name = nameField.value
    })

    typeField.addEventListener('change', function () {
      valueField.setAttribute('data-type', typeField.value)
      if (typeField.value === 'HttpFile') {
        valueField.type = 'file'
      } else {
        valueField.type = 'text'
      }
    })

    removeButton.addEventListener('click', function () {
      rowParent.removeChild(newRow)
    })

    nameField.focus()
  }

  function openTestPanel(e) {
    var id = e.target.getAttribute('data-api')
    var api = API_LIST[id]
    $('.module', testPanel).text(api.module)
    $('.name', testPanel).text(api.name)
    $('.info', testPanel).empty()
    $('.info', testPanel).append(renderUrlInfo(api))

    if (api.addition_info) {
      $('.addition-info', testPanel).html(api.addition_info).show()
    } else {
      $('.addition-info', testPanel).hide()
    }

    var table = $('table', testPanel)

    var toolRow = null
    if (api.handler_info.arguments.some(function (item) {
      return item.is_variable
    })) {
      var button = el('a', {href: 'javascript:', id: 'btn-add-test-field'}, '添加字段')
      // 有可变参数，添加字段工具行
      toolRow = el('tr', {
        'class': 'test-row--tool'
      }, [
        el('td', null, button),
        el('td'),
        el('td'),
        el('td')
      ])
      button.addEventListener('click', function () {
        addTestField(toolRow, ['post', 'put'].indexOf(api.method) !== -1)
      })
    }

    table.replaceWith(renderArgs(api.handler_info.arguments, true, toolRow))

    statusCode.empty()
    statusText.empty()
    responseContent.empty().hide()
    responseTime.empty()
    responseType.empty()
    responseLength.empty()

    testPanel.css('display', 'flex')
  }

  function renderTestResponse(response, url) {
    $('div.response', testPanel)[0].scrollIntoView()
    var contentType = response.headers['content-type']
    var data = response.data
    if (contentType.indexOf('image/') === 0) {
      var image = new Image()
      image.classList.add('response-image')
      image.src = data
      responseContent.append(image)
      responseContent.show()
      return
    }

    if (response.isText) {
      if (typeof data === 'string') {
        if (response.headers['content-type'].indexOf('text/html') === -1) {
          responseContent.html('<pre>' + data + '</pre>')
        } else {
          responseContent.html(data)
        }
      } else {
        responseContent.jsonViewer(data)
      }

      responseContent.show()
      return
    }

    // 其它的数据类型，无法预览

    // 尝试获取可能的扩展名
    // 此处使用 mime 中的名称
    // 不用保证正确性
    var match = /\/([a-z0-9]+)?/.exec(contentType)
    var ext = match ? ('.' + match[1]) : ''

    var link = document.createElement('a')
    link.href = response.data
    link.innerHTML = '点击此处存为文件'
    link.download = encodeURI(url.substr(window.location.origin.length)) + ext
    var label = document.createElement('span')
    label.innerHTML = '此类型的数据不支持预览，'
    responseContent.append(label)
    responseContent.append(link)
    responseContent.show()
  }

  $('#btn-send-test', testPanel).on('click', function () {
    var method = $('.method', testPanel).text().trim()
    var url = $('.url', testPanel).text().trim()
    sendTest(method, url)
  })

  list.on('click', '.btn-open-test', function (e) {
    openTestPanel(e)
  })
  initPanel(testPanel)
})
()
