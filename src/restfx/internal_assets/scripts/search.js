(function () {
    var input = $('#search-input')
    var keyword = ''
    var searchTimer
    var modules
    var routes
    var navs
    // 存储起来高亮的元素 Node
    // 以及高亮前的元素 Node
    // 以便于在取消高亮后，恢复原来的样子
    var hlItems = []

    window.addEventListener('keydown', function (e) {
        // F2
        // Ctrl K 查找
        if (e.keyCode !== 113 && (!e.ctrlKey || e.keyCode !== 75)) {
            return
        }
        e.preventDefault()
        e.stopPropagation()

        if (input.parent().hasClass('focused')) {
            input.blur()
        } else {
            input.focus()
        }
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
        if (e.keyCode === 13) {
            // Enter
            input.blur()
            return
        }
        var val = $(this).val()
        if (keyword === val) {
            return
        }
        // 干掉开头的空白字符
        keyword = val
        clearTimeout(searchTimer)

        searchTimer = setTimeout(function () {
            doSearch()
        }, 500)
    })

    input.on('focus', function () {
        input.parent().addClass('focused')

        setTimeout(function () {
            input.get(0).select()
        }, 100)
    })
    input.on('blur', function () {
        input.parent().removeClass('focused')
    })

    function doSearch() {
        if (!modules) {
            modules = $('li.module-item')
        }
        if (!routes) {
            routes = $('li.api-item')
        }

        if (!navs) {
            navs = $('#api-nav-list>li')
        }

        // 清除高亮词
        for (var i = 0; i < hlItems.length; i++) {
            var t = hlItems[i]
            t.b.parentElement.replaceChild(t.a, t.b)
        }
        hlItems.length = 0

        var searchKey = keyword
        // 清空关键字
        if (!searchKey) {
            $('.search-miss').removeClass('search-miss')
            modules.show()
            return
        }

        // 移除前后的空白
        searchKey = searchKey.replace(/^\s*(.+?)\s*$/, '$1')

        // 将中间的多个空白字符当成一个来进行分割
        var searchKeys = searchKey.split(/\s+?/g)

        routes.each(function () {
            var item = $(this)
            var itemContent = item.text()
            var searchExpr = resolveExpr(searchKeys)
            var hit = searchExpr.test(itemContent)
            if (hit) {
                hit = hl(item.get(0), searchKeys)
                if (hit) {
                    item.removeClass('search-miss').addClass('search-hit')
                } else {
                    item.addClass('search-miss').removeClass('search-hit')
                }
            } else {
                item.addClass('search-miss').removeClass('search-hit')
            }
        })

        modules.each(function () {
            var module = $(this)
            var moduleName = module.find('span.module-name')

            var moduleNameText = moduleName.text()
            var searchExpr = resolveExpr(searchKeys)
            var hitModule = searchExpr.test(moduleNameText)
            if (hitModule) {
                // 如果命中模块名称，那么显示模块（收起）
                moduleName.show().addClass('search-hit')
                hl(moduleName.get(0), searchKeys)
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

        setTimeout(function () {
            // 更新 navs
            navs.each(function () {
                var nav = $(this)
                nav.find('li.route-name').each(function () {
                    var route = $(this)
                    var routeId = $(this).attr('data-id')
                    var apiItem = list.find('li.api-item.api-id-' + routeId)
                    if (apiItem.hasClass('search-hit')) {
                        route.addClass('search-hit').removeClass('search-miss')
                    } else {
                        route.removeClass('search-hit').addClass('search-miss')
                    }
                })
                if (nav.find('li.route-name.search-hit').length) {
                    nav.addClass('search-hit').removeClass('search-miss')
                } else {
                    nav.removeClass('search-hit').addClass('search-miss')
                }
            })
        }, 200)
    }

    /**
     *
     * @param {Node} item
     * @param {string[]} searchKeys
     */
    function hl(item, searchKeys) {
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
                hit += hl(node, searchKeys)
            })
            return hit
        }
        var text = item.textContent
        var fragment = hlTextContent(text, searchKeys)
        hlItems.push({
            a: item, b: fragment
        })
        item.parentElement.replaceChild(fragment, item)
        return 1
    }

    function hlTextContent(content, searchKeys, fragment) {
        fragment = fragment || el('span')
        var searchExpr = resolveExpr(searchKeys)
        var exprMatches = searchExpr.exec(content)
        if (exprMatches) {
            var groups = exprMatches.groups
            var groupKeys = Object.keys(groups).sort()

            groupKeys.forEach(function (key) {
                var text = groups[key]
                if (!text) {
                    return
                }
                if (/\$hit$/.test(key)) {
                    var s = el('span', {
                        'class': 'search-hl'
                    }, text)
                    fragment.appendChild(s)
                } else {
                    var t = document.createTextNode(text)
                    fragment.appendChild(t)
                }
            })
            return fragment
        }

        for (var i1 = 0; i1 < searchKeys.length; i1++) {
            if (!content) {
                break
            }

            var key = searchKeys[i1];

            if (content === key) {
                var s = el('span', {
                    'class': 'search-hl'
                }, key)
                fragment.appendChild(s)
                content = ''
                break
            }

            content = hlKeyword(content, key, fragment)
        }
        if (content) {
            var t = document.createTextNode(content)
            fragment.appendChild(t)
        }
        return fragment
    }

    function hlKeyword(content, key, fragment) {
        key = key.toLowerCase()
        while (true) {
            if (!content) {
                return content
            }
            var idx = content.toLowerCase().indexOf(key)
            if (idx === -1) {
                return content
            }
            if (idx > 0) {
                // 未命中部分
                var missContent = content.substring(0, idx)
                var t = document.createTextNode(missContent)
                fragment.appendChild(t)
                content = content.substring(idx)
            }
            // 命中部分
            var hitContent = content.substring(0, key.length)
            var s = el('span', {
                'class': 'search-hl'
            }, hitContent)
            fragment.appendChild(s)
            content = content.substring(key.length)
        }
    }

    function resolveExpr(searchKeys) {
        var temp = []
        var index = 0
        searchKeys.forEach(function (key) {
            key = key.replace(/([[({.+*^$])/gi, '\\$1')
            temp.push('(?<g' + padIndex(index++) + '$miss>.*)')
            temp.push('(?<g' + padIndex(index++) + '$hit>' + key + ')')
        })
        temp.push('(?<g' + padIndex(index) + '$miss>.*)')
        return new RegExp(temp.join(''), 'ig')
    }

    function padIndex(num) {
        if (num < 10) {
            return '00' + num.toString()
        }
        if (num < 100) {
            return '0' + num.toString()
        }
        return num.toString()
    }
})()
