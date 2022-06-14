(function () {
    var hooks = {
        request: [],
        response: []
    }

    window.restfx = {
        _hooks: hooks,
        on: function (hookName, handler) {
            if (!hooks.hasOwnProperty(hookName)) {
                console.error('Invalid hookName "%s", expected %s', hookName, Object.keys(hooks).join('/'))
                return
            }
            hooks[hookName].push(handler)
        }
    }
})()


function loadPage() {
    // 请求数据
    var loading = $('#loading')
    loading.show()
    request('get', urlRoot + '/' + apiPrefix + '/api.json', {
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
                ]))
                list.show()
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

var all, allAnchors

function getAll() {
    if (all) {
        return all
    }
    all = $('.api-item')
    return all
}

function getAllAnchors() {
    if (allAnchors) {
        return allAnchors
    }
    allAnchors = $('a.anchor')
    return allAnchors
}

function collapseAll() {
    // getAll().removeAttr('open')
    getAll().removeClass('expanded')
    getAll().addClass('collapsed')
}

function expandAll() {
    // getAll().attr('open', '')
    getAll().addClass('expanded')
    getAll().removeClass('collapsed')
}

(function () {
    var oldHash = ''

    var app = $('#app')
    app.on('click', '#current-anchor', function () {
        $('#current-anchor').removeAttr('id')
    })

    function onHashChanged() {
        if (oldHash) {
            // 移除现有样式
            $('#current-anchor').removeAttr('id')
        }
        oldHash = window.location.hash
        var hashvalue = oldHash.substring(1)
        if (!hashvalue) {
            return
        }
        var anchors = getAllAnchors()
        for (var i = 0; i < anchors.length; i++) {
            var anchor = anchors.eq(i)
            var name = anchor.attr('name')
            if (name === hashvalue) {
                anchor.parent().attr('id', 'current-anchor')
                return
            }
        }
    }

    setTimeout(function () {
        if (("onhashchange" in window) && ((typeof document.documentMode === "undefined") || document.documentMode === 8)) {
            // 浏览器支持onhashchange事件
            window.onhashchange = onHashChanged
            onHashChanged()
        } else {
            // 不支持则用定时器检测的办法
            setInterval(function () {
                var currentHash = window.location.hash
                if (currentHash !== oldHash) {
                    onHashChanged()
                }
            }, 500);
        }
    }, 500)
})();

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
                '　　　　　　-- 开发者 wangankeji'
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
