(function () {
    var argsTable = $('table.args-table', testPanel)
    var headerTable = $('table.header-table', testPanel)
    var responseContent = $('div.response-content', testPanel)
    var responseHeader = $('table.response-header tbody', testPanel)
    var responseStatus = $('.response-status', testPanel)
    var statusCode = $('.status-code', testPanel)
    var statusText = $('.status-text', testPanel)
    var responseTime = $('.response-time', testPanel)
    var responseLength = $('.response-length', testPanel)
    var responseType = $('.response-type', testPanel)
    var linkSaveAs = $('#test-response--save-as')
    var argsJson = $('#args-json')

    panelCloseHooks.push(function () {
        request.cancelAll()
    })

    function renderResponseInfo(xhr, start) {
        var end = new Date().getTime()
        responseTime.text('耗时: ' + (end - start) + 'ms')

        responseStatus.removeClass('status-success status-failure')
        responseStatus.addClass(xhr.status === 200 ? 'status-success' : 'status-failure')

        // 渲染响应头
        responseHeader.empty()
        for (var headerName in xhr.rawHeaders) {
            responseHeader.append(el('tr', {
                'class': 'response-header--row'
            }, [
                el('td', null, headerName),
                el('td', null, decodeURI(xhr.rawHeaders[headerName]))
            ]))
        }

        if (xhr.status === 0) {
            return
        }

        statusCode.text(xhr.status)
        statusText.text(xhr.statusText)

        var type = xhr.headers['content-type'].split(';')[0]
        responseType.text('Content-Type: ' + type)

        var len = xhr.headers['content-length'] ? ((xhr.headers['content-length'] / 1024).toFixed(2) * 100) / 100 : 0
        responseLength.text('Content-Length: ' + xhr.headers['content-length'] + ' (' + len + 'KB)')
    }

    function getTableArgs() {
        var fields = Object.create(null)
        $('input.arg-value, textarea.arg-value', argsTable).each(function () {
            var field = $(this)
            field.removeClass('required')
            field = field[0]
            if (field.type === 'file') {
                fields[field.name] = {
                    value: field.files[0]
                }
            } else {
                fields[field.name] = {
                    value: field.value
                }
            }
            fields[field.name].type = field.dataset.type
        })

        // 处理数据格式
        var formData = Object.create(null)
        for (var name in fields) {
            // 忽略空的字段
            if (!name || /^\s*$/.test(name)) {
                continue
            }

            // var fieldType = fields[name].type

            formData[name] = fields[name].value
        }

        return formData
    }

    function getJsonArgs() {
        var json = formatJson()
        if (!json) {
            return
        }

        for (var name in json) {
            var val = json[name]
            if ($.isArray(val) || Object.prototype.toString.call(val) === '[object Object]') {
                json[name] = JSON.stringify(val)
            }
        }

        return json
    }

    function sendTest(method, url) {
        responseContent.empty()
        responseStatus.removeClass('status-success status-failure')
        statusCode.empty()
        statusText.empty()
        responseTime.empty()
        responseLength.empty()
        linkSaveAs.hide()
        var fields = $('.request-tab .args-types--header li.active', testPanel).attr('data-index') === '0' ?
            getTableArgs() : getJsonArgs()

        if (!fields) {
            return
        }

        responseTime.text('加载中...')

        var start = new Date().getTime()
        var option = {
            callback: function (response) {
                for (var i = 0; i < restfx._hooks.response.length; i++) {
                    var handler = restfx._hooks.response[i]
                    response = handler(method, url, response)
                    if (response === false) {
                        return
                    }
                }

                renderResponseInfo(response, start)

                if (response.status === 0) {
                    return
                }
                renderTestResponse(response, url)
            }
        }
        if (['get', 'delete'].indexOf(method) === -1) {
            option.data = new FormData()
            for (var name in fields) {
                option.data.append(name, fields[name])
            }
        } else {
            option.param = fields
        }

        var headers = {}
        headerTable.find('tr.test-row--header').each(function () {
            var row = $(this)
            if (!row.find('input[type=checkbox]').is(':checked')) {
                return
            }
            var name = row.find('input.test-header--name').val().trim()
            var value = row.find('input.test-header--value').val().trim()
            if (!name) {
                return
            }
            headers[name] = value
        })

        option.headers = headers

        for (var i = 0; i < restfx._hooks.request.length; i++) {
            var handler = restfx._hooks.request[i]
            var result = handler(method, url, option)
            if (result === false) {
                return
            }
            var returnType = Object.prototype.toString.call(result)
            if (returnType !== '[object Object]') {
                console.error('Invalid return type "%s" of "beforeRequest" ignored, a plain Object expected: %s', returnType, result)
                continue
            }
            option = result
        }

        request(method, url, option)
    }

    function addTestField(toolRow, allowForm) {
        var rowParent = toolRow.parentElement

        var nameField = el('input', {placeholder: '填写字段名称', 'class': 'arg-name'})

        var types = [
            el('option', {value: 'str'}, '字符串')
        ]

        // 是否允许表单，部分数据类型只有在允许表单时才能传输
        if (allowForm) {
            types = types.concat([
                el('option', {value: 'int'}, '整数'),
                el('option', {value: 'float'}, '小数'),
                el('option', {value: 'bool'}, '布尔值'),
                el('option', {value: 'list'}, '数组'),
                el('option', {value: 'HttpFile'}, '文件')
            ])
        }

        var typeField = el('select', {'class': 'arg-type'}, types)

        var valueField = el('input', {
            type: 'text',
            'data-type': 'str',
            'class': 'arg-value'
        })

        var removeButton = el('a', {
            href: 'javascript:',
            'class': 'btn-remove-test-field'
        }, '移除')

        var newRow = el('tr', {
            'class': 'test-row--tool'
        }, [
            el('td', null, nameField),
            el('td', null, typeField),
            el('td', null, valueField),
            el('td', null, removeButton)
        ])

        rowParent.insertBefore(newRow, toolRow)

        nameField.addEventListener('input', function () {
            valueField.name = nameField.value
        })

        typeField.addEventListener('change', function () {
            valueField.setAttribute('data-type', typeField.value)
            if (typeField.value === 'HttpFile') {
                valueField.type = 'file'
            } else {
                valueField.type = 'text'
            }
        })

        removeButton.addEventListener('click', function () {
            rowParent.removeChild(newRow)
        })

        nameField.focus()
    }

    function initHeaders() {
        var table = headerTable.find('tbody')
        // table.empty()

        if ($('#btn-add-test-header').length) {
            return
        }

        var toolRow = null

        var button = el('a', {href: 'javascript:', id: 'btn-add-test-header'}, '添加头')
        // 有可变参数，添加字段工具行
        toolRow = el('tr', {
            'class': 'test-row--tool'
        }, [
            el('td', null, button),
            el('td'),
            el('td'),
            el('td')
        ])
        button.addEventListener('click', function () {
            var removeButton = el('a', {
                href: 'javascript:',
                'class': 'btn-remove-test-header'
            }, '移除')
            var newRow = el('tr', {'class': 'test-row--header'}, [
                el('td', null, el('input', {
                    type: 'checkbox', 'class': 'test-header--checkbox', checked: 'checked'
                })),
                el('td', null, el('input', {
                    type: 'text', 'class': 'test-header--name arg-value', maxlength: 1024
                })),
                el('td', null, el('input', {
                    type: 'text', 'class': 'test-header--value arg-value', maxlength: 1024
                })),
                el('td', null, removeButton)
            ])
            table.get(0).insertBefore(newRow, toolRow)
            removeButton.addEventListener('click', function () {
                newRow.parentElement.removeChild(newRow)
            })
        })
        table.append(toolRow)
        // // 默认添加3行
        // button.click()
        // button.click()
        // button.click()
    }

    function openTestPanel(e) {
        var id = e.target.getAttribute('data-api')
        var api = API_LIST[id]
        $('.module', testPanel).text(api.module)
        $('.name', testPanel).text(api.name)
        $('.url-info .method', testPanel).text(api.method)
        $('.url-info .url', testPanel).val(urlRoot + '/' + apiPrefix + api.path)

        if (api.addition_info) {
            $('.addition-info', testPanel).html(api.addition_info).show()
        } else {
            $('.addition-info', testPanel).hide()
        }

        // 先中第一个 tab
        $('.tabs-layout', testPanel).each(function () {
            $(this).find('li').first().click()
        })

        // $('table.args-table', testPanel).remove()

        var toolRow = null
        if (api.handler_info.arguments.some(function (item) {
            return item.is_variable
        })) {
            var button = el('a', {href: 'javascript:', id: 'btn-add-test-field'}, '添加字段')
            // 有可变参数，添加字段工具行
            toolRow = el('tr', {
                'class': 'test-row--tool'
            }, [
                el('td', null, button),
                el('td'),
                el('td'),
                el('td')
            ])
            button.addEventListener('click', function () {
                addTestField(toolRow, ['post', 'put'].indexOf(api.method) !== -1)
            })
        }

        var tableParent = argsTable.parent()
        argsTable.remove()
        argsTable = $(renderArgRows(api.handler_info.arguments, true, toolRow))
        argsTable.addClass('tabs-item active')
        tableParent.prepend(argsTable)
        // table.append()

        // 渲染初始化的 JSON 内容
        argsJson.val('')
        renderJsonArgs(api.handler_info.arguments)

        initHeaders()

        statusCode.empty()
        statusText.empty()
        responseContent.empty()
        responseHeader.empty()
        responseTime.empty()
        responseType.empty()
        responseLength.empty()
        linkSaveAs.hide()

        testPanel.css('display', 'flex')
    }

    function renderJsonArgs(args) {
        var json = {}

        args.forEach(function (arg) {
            if (arg.is_variable) {
                return
            }
            json[arg.name] = arg['default']
        })

        argsJson.val(JSON.stringify(json, null, 2))
    }

    function renderTestResponse(response, url) {
        $('div.response', testPanel)[0].scrollIntoView()
        var contentType = response.headers['content-type']
        var data = response.data
        if (contentType.indexOf('image/') === 0) {
            var image = new Image()
            image.classList.add('response-image')
            image.src = data
            responseContent.append(image)
        } else if (response.isText) {
            var previewable = false
            if (typeof data === 'string') {
                // 如果数据长度超过了 1M，那么不预览，仅提供下载
                if (data.length < 1024 * 1024) {
                    previewable = true
                    if (contentType.indexOf('text/html') === -1) {
                        responseContent.html('<pre>' + data + '</pre>')
                    } else {
                        responseContent.html(data)
                    }
                }
            } else {
                // 如果数据长度超过了 1M，那么不预览，仅提供下载
                if (response.length < 1024 * 1024) {
                    previewable = true
                    responseContent.jsonViewer(data)
                } else {
                    // 处理成字符串，以便后面生成 base64
                    data = JSON.stringify(data)
                }
            }
            if (!previewable) {
                var label = document.createElement('span')
                label.innerHTML = '数据大小超过 1M，不支持预览'
                responseContent.append(label)
            }
            // 处理一下，交由 另存为 使用
            data = 'data:' + contentType.split(';')[0] + ';base64,' + Base64.encode(data)
        } else {
            var label = document.createElement('span')
            label.innerHTML = '此类型的数据不支持预览，'
            responseContent.append(label)
        }

        // 其它的数据类型，无法预览
        // 首先检查 content-disposition 头
        // 如果找不到
        // 尝试获取可能的扩展名
        // 此处使用 mime 中的名称
        // 不用保证正确性
        var disposition = response.headers['content-disposition']
        var match = /\/([a-z\d]+)?/.exec(contentType)
        var ext = match ? ('.' + match[1]) : ''
        var filename = disposition || encodeURI(url.substring(window.location.origin.length)) + ext
        if (disposition) {
            filename = disposition.split('filename=')[1]
            match = /^=\?utf-8\?B\?(.+?)\?=/.exec(filename)
            if (match) {
                // 处理奇怪的火狐
                try {
                    filename = Base64.decode(match[1])
                } catch (e) {
                    // 解不出来就算了
                }
            } else {
                filename = decodeURI(filename)
            }
        }

        linkSaveAs.attr('href', data)
        linkSaveAs.attr('download', filename)
        linkSaveAs.show()
    }

    $('#btn-send-test', testPanel).on('click', function () {
        var method = $('.method', testPanel).text().trim()
        var url = $('.url', testPanel).val().trim()
        sendTest(method, url)
    })

    list.on('click', '.btn-open-test', function (e) {
        openTestPanel(e)
    })

    var tabsHeader = $('.tabs-header')
    tabsHeader.on('click', 'li[data-index]', function () {
        var idx = this.dataset.index
        $(this).addClass('active').siblings().removeClass('active')
        $(this).parent().next().children().eq(idx).addClass('active').siblings().removeClass('active')
    })

    tabOverride.set(argsJson)
    tabOverride.tabSize(2)

    argsJson.on('focus', function () {
        $('.args-json--tip', testPanel).text('').removeClass('error')
    })

    function formatJson() {
        var tip = $('.args-json--tip', testPanel).text('').removeClass('error').removeClass('ok')

        var content = argsJson.val()
        try {
            if (!content) {
                throw new Error('请输入参数')
            }
            var obj = JSON.parse(content)
            argsJson.val(JSON.stringify(obj, null, 2))
            if ($.isArray(obj)) {
                throw new Error('参数只能是对象，不能是数组')
            }
            tip.text('格式正确').addClass('ok')
            setTimeout(function () {
                tip.text('')
            }, 1000)
            return obj
        } catch (e) {
            tip.text(e.message).addClass('error')
            return null
        }
    }

    $('#json-tool--format').on('click', formatJson)

    initPanel(testPanel)
})
()
