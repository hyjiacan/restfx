function loadPage() {
  // 请求数据
  document.querySelector('#loading').style.display = 'block'
  xhr('post', urlRoot + '/' + apiPrefix, {
    callback: function(response) {
      if (response.status !== 200) {
        list.innerHTML = response.data
        return
      }
      var data = response.data
      render(list, typeof data === 'string' ? JSON.parse(data) : data)
    }
  })

  var app = document.querySelector('#app')
  var btBtn = document.querySelector('#btn-back-to-top')
  var toggleTimer = -1

  app.addEventListener('scroll', function() {
    clearTimeout(toggleTimer)

    toggleTimer = setTimeout(function() {
      if (app.scrollTop === 0) {
        btBtn.style.display = 'none'
      } else {
        btBtn.style.display = 'flex'
      }
    }, 300)
  })

  btBtn.addEventListener('click', function() {
    app.scrollTop = 0
  })
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
  // 检测万恶的 IE
  if (!!window.ActiveXObject || "ActiveXObject" in window) {
    var matchIE = /^.+?MSIE\s(.+?);.+?Trident.+$/.exec(window.navigator.userAgent)

    // IE11 没有 MSIE 串
    var ieVersion = matchIE ? parseFloat(matchIE[1]) : 11

    var tip = document.getElementById('ie-tip')
    tip.onclick = function() {
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
    }
    if (ieVersion < 10) {
      tip.innerHTML = '恶心提示: 此页面不支持 <b>IE9及更低版本的IE浏览器</b>，请更换浏览器以获得更好的使用体验！'
      tip.style.display = 'block'
      return
    }
    tip.innerHTML = '恶心提示: 此页面对 <b>IE浏览器</b> 不友好，请更换浏览器以获得更好的使用体验！'
    tip.style.display = 'block'
  }

  loadPage()
})();