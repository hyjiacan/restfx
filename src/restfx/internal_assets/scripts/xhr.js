(function(){
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
    xhr.send(options.data)
  }

  /**
   *
   * @param {XMLHttpRequest} xhr
   * @returns {headers: {}, data: string}
   */
  function getResponse (xhr) {
    var data = xhr.responseText
    var headers = Object.create(null)
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

  window.xhr = request
})()