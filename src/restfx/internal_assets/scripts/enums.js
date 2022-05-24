(function () {
    // enumPanel
    var enumList = $('#enum-list')
    var rendered = false

    initPanel(enumPanel)

    function renderEnums() {
        enumList.empty()
        window.apiData.enums.forEach(function (enumType) {
            var el = renderEnum(enumType)
            enumList.append(el)
        })
    }

    function renderEnum(enumType) {
        var header = el('div', {
            'class': 'enum-name',
            id: 'enum-' + enumType.name.toLowerCase()
        }, enumType.name)
        var comment = el('p', {
            'class': 'comment enum-comment route-description'
        }, enumType.comment)
        var rows = enumType.items.map(function (item) {
            return el('tr', null, [
                el('td', {'class': 'enum--item-name'}, el('code', null, item.name)),
                el('td', {'class': 'enum--item-value'}, item.value),
                el('td', {'class': 'comment enum--item-comment'}, item.comment)
            ])
        })
        rows.unshift(
            el('tr', null, [
                el('th', null, '名称'),
                el('th', null, '值'),
                el('th', null, '备注'),
            ]),
        )
        var table = el('table', {
            'class': 'enum-table'
        }, rows)
        return el('div', {
            'class': 'enum-type'
        }, [
            header, comment, table
        ])
    }

    $('#btn-show-enums-panel').click(function () {
        if (!rendered) {
            renderEnums()
            rendered = true
        }
        enumPanel.css('display', 'flex')
    })

    list.on('click', '.arg-type.is-enum', function () {
        $('#btn-show-enums-panel').click()
        var target = '#enum-' + $(this).attr('data-type').toLowerCase()
        var item = $(target)
        if (!item) {
            return
        }
        setTimeout(function () {
            item.get(0).scrollIntoView({
                behavior: 'smooth'
            })
            item.addClass('highlight')
            setTimeout(function () {
                item.removeClass('highlight')
            }, 1000)
        }, 200)
    })
})()