(function () {
  function serializeParams(url, params) {
    var temp = []
    for (var key in params) {
      temp.push(key + '=' + params[key])
    }
    if (url.indexOf('?') === -1) {
      url += '?'
    }
    var and = ''
    if (url.indexOf('&') !== -1) {
      and = '&'
    }
    url += and + temp.join('&')
    return url
  }

  function request(method, url, options) {
    var xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        getResponse(xhr, options.callback)
      }
    }
    if (options.param) {
      url = serializeParams(url, options.param)
    }
    xhr.responseType = 'arraybuffer'
    xhr.open(method.toUpperCase(), url, true)
    xhr.setRequestHeader('accept', 'application/json;text/*;image/*;*/*')
    xhr.setRequestHeader('x-requested-with', 'XMLHttpRequest')
    if (options.headers) {
      for (var headerName in options.headers) {
        xhr.setRequestHeader(headerName, options.headers[headerName])
      }
    }
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
    var rawHeaders = Object.create(null)
    xhr
      .getAllResponseHeaders()
      .split('\r\n')
      .forEach(function (item) {
        var temp = item.trim().split(':')
        if (!temp[0]) {
          return
        }
        var hn = temp[0].trim()
        var hv = (temp[1] || '').trim()
        headers[hn] = hv
        rawHeaders[hn] = hv
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
        rawHeaders: rawHeaders,
        status: xhr.status,
        statusText: xhr.statusText
      })
    })
  }

  window.xhr = request
})()
