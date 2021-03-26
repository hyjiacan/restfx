function loadPage() {
  // 请求数据
  var loading = $('#loading')
  loading.show()
  xhr('post', urlRoot + '/' + apiPrefix, {
    callback: function (response) {
      var data = response.data
      if (response.status !== 200) {
        loading.hide()

        var content = ''
        if (response.status) {
          content = response.headers['content-type'].indexOf('text/html') === -1 ?
            el('pre', null, data) : el('p', null, data)
        }

        list.append(el('div', {
          'class': 'load-error'
        }, [
          el('h3', null, response.status ? response.statusText : 'No responding'),
          content
        ])).show()
        return
      }
      render(list, typeof data === 'string' ? JSON.parse(data) : data)
    }
  })

  var app = $('#app')
  var btBtn = $('#btn-back-to-top')
  var toggleTimer = -1

  app.on('scroll', function () {
    clearTimeout(toggleTimer)

    toggleTimer = setTimeout(function () {
      if (app.scrollTop() === 0) {
        btBtn.hide()
      } else {
        btBtn.css('display', 'flex')
      }
    }, 300)
  })

  btBtn.on('click', function () {
    app.scrollTop(0)
  })
}

var all

function getAll() {
  if (all) {
    return all
  }
  all = $('details')
  return all
}

function collapseAll() {
  getAll().removeAttr('open')
}

function expandAll() {
  getAll().attr('open', '')
}

(function () {
  // 检测万恶的 IE
  if (!!window.ActiveXObject || 'ActiveXObject' in window) {
    var matchIE = /^.+?MSIE\s(.+?);.+?Trident.+$/.exec(window.navigator.userAgent)

    // IE11 没有 MSIE 串
    var ieVersion = matchIE ? parseFloat(matchIE[1]) : 11

    var tip = $('#ie-tip')
    tip.on('click', function () {
      // 2021.01.20
      alert([
        '　　　　　IE之苦　　　　　　',
        '',
        '未知何缘何故，仍为 IE 服务。',
        '回看谷歌火狐，似乎形同陌路。',
        '却说如今微软，踏上EDGE新途。',
        '不与 IE 为伍，不受 IE 束缚。',
        '遵从前端标准，管他领导客户。',
        '愿君脱离苦海，独自潇洒如故。',
        '',
        '　　　　　　-- 开发者 hyjiacan'
      ].join('\n'))
    })
    if (ieVersion < 10) {
      tip.html('恶心提示: 此页面不支持 <b>IE9及更低版本的IE浏览器</b>，请更换浏览器以获得更好的使用体验！').show()
      return
    }
    tip.html('恶心提示: 此页面对 <b>IE浏览器</b> 不友好，请更换浏览器以获得更好的使用体验！').show()
  }

  loadPage()
})()
