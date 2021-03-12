(function () {
  function parseChsNumber(value) {
    var chs = '零一二三四五六七八九'
    return value.toString().split('').map(function (item) {
      return chs[parseInt(item)]
    }).join('')
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
    return '返回:' + (route.handler_info.return_description || '-')
  }

  function renderArg(arg) {
    var argName = arg.name
    if (arg.alias) {
      argName += '/' + arg.alias
    }
    var argType
    if (arg.is_variable) {
      arg.has_annotation = true
      argName = '**' + argName
      argType = 'VAR_KEYWORD'
    } else if (arg.has_annotation) {
      argType = arg.annotation_name
    } else {
      argType = '-'
    }

    return [
      argName,
      arg.has_annotation ? code(argType) : argType,
      arg.has_default ? code(getArgDefaultValue(arg)) : '-',
      arg.comment ? arg.comment : '-'
    ]
  }

  function renderArgs(args) {
    if (!args || !args.length) {
      return '参数信息: _无_'
    }

    var table = [
      '参数信息',
      '',
      '|参数名称/别名|参数类型|默认值|描述|',
      '|---|---|---|---|'
    ]

    for (var i = 0; i < args.length; i++) {
      var arg = args[i]
      // 始终不显示 HttpRequest 参数 和 注入参数
      if (arg.annotation_name === 'HttpRequest' || arg.is_injected) {
        continue
      }
      table.push('|' + renderArg(arg).join('|') + '|')
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
      h(3, index + '. [路由] ' + (route.name || '_<未命名>_')),
      '描述: ' + (route.handler_info.description || '_无_'),
      '',
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
      h(2, parseChsNumber(index + 1) + '、 [模块] ' + (moduleName || '_<未命名>_'))
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
      '> Powered by [',
      data.meta.name,
      '@',
      data.meta.version,
      '](',
      data.meta.url + '?from=dist.md',
      '&version=' + data.meta.version,
      ')'
    ].join(''))

    // 在结尾处追加空行
    content.push('')
    var md = content.join('\n')

    // console.log(md)
    // return

    var form = document.querySelector('#export-proxy')
    form.setAttribute('action', urlRoot + '/' + apiPrefix + '?export=md')
    document.querySelector('#md-content').value = Base64.encode(md)
    form.submit()
  }

  document.querySelector('#btn-export').addEventListener('click', function () {
    if (!window.apiData) {
      alert('数据暂不可用，请稍后再试！')
      return
    }
    setTimeout(function () {
      doExport(window.apiData)
    }, 100)
  })
})()
