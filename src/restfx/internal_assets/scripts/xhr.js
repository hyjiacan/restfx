(function () {
  var requestId = 0
  var pendingRequests = {}

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
        if (pendingRequests.hasOwnProperty(xhr.requestId)) {
          delete pendingRequests[xhr.requestId]
        }
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
    requestId++
    xhr.requestId = requestId.toString()
    pendingRequests[xhr.requestId] = xhr
    return xhr
  }

  request.cancel = function (xhr) {
    if (!xhr || !xhr.requestId) {
      return
    }
    var id = xhr.requestId
    if (pendingRequests.hasOwnProperty(id)) {
      try {
        pendingRequests[id].abort()
      } catch (e) {
      }
      delete pendingRequests[id]
    }
  }

  request.cancelAll = function () {
    var ids = []
    for (var k in pendingRequests) {
      ids.push(k)
    }
    ids.forEach(function (id) {
      try {
        pendingRequests[id].abort()
      } catch (e) {
      }
      delete pendingRequests[id]
    })
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
        var hn = temp.shift().trim()
        var hv = temp.join(':').trim()
        headers[hn] = hv
        rawHeaders[hn] = hv
      })
    var contentType = headers['content-type']
    if (!contentType) {
      headers['content-type'] = contentType = ''
    }

    var isText = contentType.indexOf('text/') !== -1 || contentType.indexOf('/json') !== -1

    decodeResponse(data, isText, function (data) {
      var dataLength = parseInt(headers['content-length'])
      if (isText) {
        try {
          data = JSON.parse(data)
        } catch (e) {
        }
      }
      callback({
        data: data,
        length: dataLength,
        isText: isText,
        headers: headers,
        rawHeaders: rawHeaders,
        status: xhr.status,
        statusText: xhr.statusText
      })
    })
  }

  window.request = request
})()
