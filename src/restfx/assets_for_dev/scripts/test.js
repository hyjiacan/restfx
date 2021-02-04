(function() {
  function sendTest(method, url) {
    testPanel.querySelector('div.response-content').innerHTML = ''
    testPanel.querySelector('textarea.response-content').value = ''
    testPanel.querySelector('div.response-content').style.display = 'none'
    testPanel.querySelector('textarea.response-content').style.display = 'none'
    testPanel.querySelector('.response-status').classList.remove('status-success', 'status-failed')
    testPanel.querySelector('.status-code').textContent = ''
    testPanel.querySelector('.status-text').textContent = ''
    testPanel.querySelector('.response-time').textContent = ''

    var fields = Object.create(null)
    var temp = testPanel.querySelectorAll('input.arg-value')
    for (var index = 0; index < temp.length; index++) {
      var field = temp[index]
//      if (field.required && !field.value) {
//        field.classList.add('required')
//        return
//      }
      field.classList.remove('required')
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
    }
    temp = testPanel.querySelectorAll('textarea.arg-value')
    for (var index = 0; index < temp.length; index++) {
      var field = temp[index]
//      if (field.required && !field.value) {
//        field.classList.add('required')
//        return
//      }
      field.classList.remove('required')
      fields[field.name] = {
        value: field.value,
        type: field.dataset.type
      }
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

    // 处理数据格式
    var formData = Object.create(null)
    for (var name in fields) {
      // 忽略空的字段
      if (!name || /^\s*$/.test(name)) {
        continue
      }

      var fieldType = fields[name].type
      var fieldValue = fields[name].value

      // 忽略值为空的字段
      if (!fieldValue) {
        continue
      }

      switch(fieldType) {
        case 'int':
          fieldValue = parseInt(fieldValue)
          break
        case 'float':
          fieldValue = parseFloat(fieldValue)
          break
        case 'bool':
          fieldValue = fieldValue === 'true'
          break
      }
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
        el('option', {value: 'HttpFile'}, '文件'),
      ])
    }

    var typeField = el('select', {'class': 'arg-type'}, types)

    var valueField = el('input', {
      type: 'text',
      'data-type': 'int',
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

    nameField.addEventListener('input', function() {
      valueField.name = nameField.value
    })

    typeField.addEventListener('change', function() {
      valueField.setAttribute('data-type', typeField.value)
      if (typeField.value === 'HttpFile') {
        valueField.type = 'file'
      } else {
        valueField.type = 'text'
      }
    })

    removeButton.addEventListener('click', function() {
      rowParent.removeChild(newRow)
    })

    nameField.focus()
  }

  function openTestPanel (e) {
    var id = e.target.getAttribute('data-api')
    var api = API_LIST[id]
    testPanel.querySelector('.module').textContent = api.module
    testPanel.querySelector('.name').textContent = api.name
    testPanel.querySelector('.info').innerHTML = ''
    testPanel.querySelector('.info').appendChild(renderUrlInfo(api))

    if(api.addition_info){
      testPanel.querySelector('.addition-info').innerHTML = api.addition_info
      testPanel.querySelector('.addition-info').style.display = 'block'
    } else {
      testPanel.querySelector('.addition-info').style.display = 'none'
    }

    var table = testPanel.querySelector('table')
    var tableContainer = table.parentElement

    var toolRow = null
    if (api.handler_info.arguments.some(function(item) {
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
      button.addEventListener('click', function() {
        addTestField(toolRow, ['post', 'put'].indexOf(api.method) !== -1)
      })
    }

    tableContainer.replaceChild(renderArgs(api.handler_info.arguments, true, toolRow), table)

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

    testPanel.querySelector('div.response').scrollIntoView()

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
  testPanel.querySelector('#btn-send-test').addEventListener('click', function () {
    var method = testPanel.querySelector('.method').textContent.trim()
    var url = testPanel.querySelector('.url').textContent.trim()
    sendTest(method, url)
  })
  document.body.addEventListener('click', function (e) {
    if (e.target.classList.contains('btn-open-test')) {
      openTestPanel(e)
    }
  })
  initPanel(testPanel)
})();