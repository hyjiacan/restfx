function renderNavModule(moduleName, routes) {
    var navs = $('#api-nav-list')

    var hasName = !!moduleName
    var routeElements = el('ul')

    routes.forEach(function (route) {
        routeElements.appendChild(el('li', {
            'class': 'route-name',
            'data-id': route.__id__
        }, el('a', {
            href: '#' + encodeURI(route.method.toLowerCase() + ':' + route.path),
            title: route.description
        }, route.name || '<未命名>')))
    })

    var moduleElement = el('li', {
        'class': 'module-name ' + (hasName ? '' : 'unnamed-item'),
    }, [el('a', {
        href: '#' + encodeURI(hasName ? moduleName : '__un_named_module__')
    }, hasName ? moduleName : '<未命名>'), routeElements])

    navs.append(moduleElement)
}

(function () {
    var navCollapsedClass = 'nav-collapsed'
    var nav = $('#api-nav')
    var header = nav.find('.header')
    var collapseBtn = header.find('small')
    var app = $('#app')

    collapseBtn.click(function () {
        app.addClass(navCollapsedClass)
    })

    header.find('span').click(function () {
        if (!app.hasClass(navCollapsedClass)) {
            return
        }
        app.removeClass(navCollapsedClass)
    })
})()
