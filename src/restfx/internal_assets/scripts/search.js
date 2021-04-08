(function () {
  var input = $('#search-input')
  var keyword = ''
  var searchTimer
  var modules
  var routes
  // 存储起来高亮的元素 Node
  // 以及高亮前的元素 Node
  // 以便于在取消高亮后，恢复原来的样子
  var hlItems = []

  window.addEventListener('keydown', function (e) {
    if (!e.ctrlKey || e.keyCode !== 70) {
      return
    }
    e.preventDefault()
    input.focus()
    return false
  })

  input.keyup(function (e) {
    if (e.keyCode === 27) {
      // ESC
      input.blur()
      input.val('')
      keyword = ''
      doSearch()
      return
    }
    var val = $(this).val()
    if (keyword === val) {
      return
    }
    // 干掉开头的空白字符
    keyword = val.replace(/^\s+/, '')
    clearTimeout(searchTimer)

    searchTimer = setTimeout(function () {
      doSearch()
    }, 500)
  })

  function doSearch() {
    if (!modules) {
      modules = $('li.module-item')
    }
    if (!routes) {
      routes = $('li.api-item')
    }

    // 清除高亮词
    for (var i = 0; i < hlItems.length; i++) {
      var t = hlItems[i]
      t.b.parentElement.replaceChild(t.a, t.b)
    }
    hlItems.length = 0
    // 清空关键字
    if (!keyword) {
      $('.search-miss').removeClass('search-miss')
      modules.show()
      return
    }

    routes.each(function () {
      var item = $(this)
      if (item.text().indexOf(keyword) === -1) {
        item.addClass('search-miss').removeClass('search-hit')
      } else {
        item.removeClass('search-miss').addClass('search-hit')
        hl(item.get(0))
      }
    })

    modules.each(function () {
      var module = $(this)
      if (module.find('.search-hit').length) {
        module.show().find('details').prop('open', 'open')
      } else {
        module.hide()
      }
    })
  }

  /**
   *
   * @param {Node} item
   */
  function hl(item) {
    if (item.nodeType !== HTMLElement.TEXT_NODE) {
      var children = item.childNodes
      if (!children.length) {
        return
      }
      children.forEach(function (node) {
        hl(node)
      })
      return
    }
    var text = item.textContent
    var temp = text.split(keyword)
    // 没有命中
    if (temp.length === 1) {
      return
    }
    var fragment = el('span')
    for (var i = 0; i < temp.length; i++) {
      var t = document.createTextNode(temp[i])
      fragment.appendChild(t)
      if (i === temp.length - 1) {
        break
      }
      var s = el('span', {
        'class': 'search-hl'
      }, keyword)
      fragment.appendChild(s)
    }
    hlItems.push({
      a: item,
      b: fragment
    })
    item.parentElement.replaceChild(fragment, item)
  }
})()
