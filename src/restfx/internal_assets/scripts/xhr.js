(function () {
  function serializeParams(params) {
    var temp = []
    for (var key in params) {
      temp.push(key + '=' + params[key])
    }
    return '?' + temp.join('&')
  }

  function request(method, url, options) {
    var xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        getResponse(xhr, options.callback)
      }
    }
    if (options.param) {
      url += serializeParams(options.param)
    }
    xhr.responseType = 'arraybuffer'
    xhr.open(method.toUpperCase(), url, true)
    xhr.setRequestHeader('accept', 'application/json;text/*;image/*;*/*')
    xhr.setRequestHeader('x-requested-with', 'XMLHttpRequest')
    xhr.send(options.data)
  }

  function decodeResponse(data, asText, callback) {
    var reader = new FileReader()
    var blob = new Blob([data])
    if (asText) {
      reader.readAsText(blob)
    } else {
      reader.readAsDataURL(blob)
    }
    reader.onload = function () {
      callback(reader.result)
    }
  }

  /**
   *
   * @param {XMLHttpRequest} xhr
   * @param callback
   * @returns {{headers: {}, data: string}}
   */
  function getResponse(xhr, callback) {
    var data = xhr.response
    var headers = Object.create(null)
    xhr
      .getAllResponseHeaders()
      .split('\r\n')
      .forEach(function (item) {
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

    var isText = contentType.indexOf('text/') !== -1 || contentType.indexOf('/json') !== -1

    decodeResponse(data, isText, function (data) {
      if (isText) {
        try {
          data = JSON.parse(data)
        } catch (e) {
        }
      }
      callback({
        data: data,
        isText: isText,
        headers: headers,
        status: xhr.status,
        statusText: xhr.statusText
      })
    })
  }

  window.xhr = request
})()
