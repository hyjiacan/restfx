(function () {
  function parseChsNumber(num) {
    var keys = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九']
    var count = ['', '十', '百', '千']
    var str = ''
    var nums = num.toString().split('').reverse()

    nums.map(function (value, index) {
      str = keys[value] +
        (value == 0 ? '' : count[index > 3 ? index % 4 : index]) +
        (index == 4 ? '万' : '') +
        str
    })

    /*
     * 需要去掉的零：
     * 1.后面跟着零的零
     * 2.最后连续的零
     * 3.万前面的零
     *
     * 将 一十 开头的处理成 十
     */
    return str.replace(/^一(?=十)|零(?=零)|零$|零(?=万)/g, '')
    // ————————————————
    // 版权声明：本文为CSDN博主「web_wyj」的原创文章，遵循CC 4.0 BY-SA版权协议，转载请附上原文出处链接及本声明。
    // 原文链接：https://blog.csdn.net/web_wyj/article/details/79477769
  }

  function formatCommentItem(item, isArg, seperator) {
    if (item.type === 'code') {
      if (isArg) {
        return seperator + '`' + $.trim(item.lines.join('').replace(/\n/g, ' ')) + '`' + seperator
      }
      return seperator + seperator + '```' + seperator +
        $.trim(item.lines.join('')) + seperator + '```' + seperator
    }
    return item.lines.map(function (line) {
      return line.replace(/\t/g, '    ')
    }).join('')
  }

  function formatComment(comment, isArg) {
    var seperator = isArg ? '<br/>' : '\n'
    if (Object.prototype.toString.call(comment) !== '[object Array]') {
      return comment
    }
    var result = comment.map(function (item) {
      return formatCommentItem(item, isArg, seperator)
    }).join('')
    return $.trim(result).replace(/\n/g, seperator + (isArg ? '' : '> '))
  }

  function padIndex(index, width) {
    index = index.toString()
    var padWidth = width - index.length
    if (padWidth <= 0) {
      return index
    }
    for (var i = 0; i < padWidth; i++) {
      index = '0' + index
    }
    return index
  }

  function h(level, content) {
    var data = []
    for (var i = 0; i < level; i++) {
      data.push('#')
    }
    return data.join('') + ' ' + content + '\n'
  }

  function code(content) {
    return ' `' + content + '` '
  }

  function codeblock(content, lang) {
    return [
      '```' + (lang || ''),
      content,
      '```\n'
    ].join('\n')
  }

  function renderReturn(route) {
    return '> 返回:' + formatComment(route.handler_info.return_description || '-', false)
  }

  function renderArg(arg) {
    var argName = arg.name
    if (arg.alias) {
      argName += '/' + arg.alias
    }
    var argType
    if (arg.is_variable) {
      arg.has_annotation = true
      argName = '...' + argName
      argType = 'variable'
    } else if (arg.has_annotation) {
      argType = arg.annotation_name
    } else {
      argType = '-'
    }

    return [
      argName,
      arg.has_annotation ? code(argType) : argType,
      arg.has_default ? code(getArgDefaultValue(arg)) : '-',
      formatComment(arg.comment || '-', '<br/>', true)
    ]
  }

  function renderArgs(args) {
    if (!args || !args.length) {
      return '参数信息: _无_'
    }

    var table = [
      '|参数名称/别名|参数类型|默认值|描述|',
      '|---|---|---|---|'
    ]

    for (var i = 0; i < args.length; i++) {
      table.push('|' + renderArg(args[i]).join('|') + '|')
    }

    return table.join('\n')
  }

  function renderUrlInfo(route) {
    return codeblock([
      route.method.toUpperCase() + ' ' + urlRoot,
      apiPrefix,
      route.path.substring(1)
    ].join('/'))
  }

  function renderRoute(route, index) {
    return [
      h(3, index + '. ' + (route.name || '_<未命名>_')),
      route.handler_info.description ?
        '\n> ' + formatComment(route.handler_info.description, false) + '\n' : '',
      renderUrlInfo(route),
      route.addition_info ? (route.addition_info + '\n') : '',
      renderArgs(route.handler_info.arguments),
      '',
      renderReturn(route),
      ''
    ].join('\n')
  }

  function renderModule(index) {
    var moduleName = window.apiData.moduleNames[index]
    var routes = window.apiData.modules[moduleName]

    var data = [
      h(2, parseChsNumber(index + 1) + '、' + (moduleName || '_<未命名>_'))
    ]

    var routeCount = routes.length
    var routeIndexWidth = routeCount.toString().length

    for (var i = 0; i < routeCount; i++) {
      data.push(renderRoute(routes[i], padIndex(i + 1, routeIndexWidth)))
    }

    return data.join('\n')
  }

  function doExport(data) {
    var content = []

    content.push(h(1, data.name))
    content.push('---')
    content.push('')

    var moduleCount = data.moduleNames.length

    for (var i = 0; i < moduleCount; i++) {
      content.push(renderModule(i))
    }

    content.push('')
    content.push('---')
    content.push('')
    content.push([
      'Powered by ',
      '[',
      data.meta.name,
      '@',
      data.meta.version,
      ']',
      '(',
      data.meta.url + '?from=dist.md',
      '&version=' + data.meta.version,
      ')'
    ].join(''))

    // 在结尾处追加空行
    content.push('')
    var md = content.join('\n')

    // console.log(md)

    var form = $('#export-proxy')
    form.attr('action', urlRoot + '/' + apiPrefix + '/export')
    $('#md-content').val(Base64.encode(md))
    form.submit()
  }

  $('#btn-export').on('click', function () {
    if (!window.apiData) {
      alert('数据暂不可用，请稍后再试！')
      return
    }
    setTimeout(function () {
      doExport(window.apiData)
    }, 100)
  })
})()
