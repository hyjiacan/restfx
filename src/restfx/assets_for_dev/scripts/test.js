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

    var fields = {}
    var temp = testPanel.querySelectorAll('input.arg-value')
    for (var index = 0; index < temp.length; index++) {
      var field = temp[index]
      if (field.required && !field.value) {
        field.classList.add('required')
        return
      }
      field.classList.remove('required')

      if (field.type === 'file') {
        fields[field.name] = field.files[0]
      } else {
        fields[field.name] = field.value
      }
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

    if (['get', 'delete'].indexOf(method) === -1) {
      option.data = new FormData()
      for (var name in fields) {
        option.data.append(name, fields[name])
      }
    } else {
      option.param = fields
    }

    xhr(method, url, option)
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