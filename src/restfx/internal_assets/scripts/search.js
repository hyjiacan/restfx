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
    // Ctrl K 查找
    if (!e.ctrlKey || e.keyCode !== 75) {
      return
    }
    e.preventDefault()
    $('#app').scrollTop(0)
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
        var hit = hl(item.get(0))
        if (hit) {
          item.removeClass('search-miss').addClass('search-hit')
        } else {
          item.addClass('search-miss').removeClass('search-hit')
        }
      }
    })

    modules.each(function () {
      var module = $(this)
      var moduleName = module.find('span.module-name')
      var hitModule = moduleName.text().indexOf(keyword) !== -1
      if (hitModule) {
        // 如果命中模块名称，那么显示模块（收起）
        moduleName.show().addClass('search-hit')
        hl(moduleName.get(0))
        module.find('.search-miss').removeClass('search-miss')
        module.show().find('details').prop('open', false)
      } else {
        moduleName.removeClass('search-hit')
      }

      if (module.find('.api-list .search-hit').length) {
        // 如果命中了路由，那么展开模块
        module.show().find('details').prop('open', 'open')
      } else if (!hitModule) {
        // 即没有命中模块名称，也没有命中路由，隐藏模块
        module.hide()
      }
    })
  }

  /**
   *
   * @param {Node} item
   */
  function hl(item) {
    var hit = 0
    if (item.tagName === 'BUTTON') {
      return 0
    }
    if (item.nodeType !== HTMLElement.TEXT_NODE) {
      var children = item.childNodes
      if (!children.length) {
        return 0
      }
      children.forEach(function (node) {
        hit += hl(node)
      })
      return hit
    }
    var text = item.textContent
    var temp = text.split(keyword)
    // 没有命中
    if (temp.length === 1) {
      return 0
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
    return 1
  }
})()
