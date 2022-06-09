(function () {
    // enumPanel
    var enumList = $('#enum-list')
    var rendered = false

    initPanel(enumPanel)

    function renderEnums() {
        enumList.empty()
        var count = 0
        var total = window.apiData.enums.length
        window.apiData.enums.forEach(function (enumType) {
            var index = (count + 1).toString() + '/' + total.toString()
            var el = renderEnum(enumType, index)
            enumList.append(el)
            count++
        })
        return count
    }

    function renderEnum(enumType, index) {
        var header = el('div', {
            'class': 'enum-title',
            id: 'enum-' + enumType.name.toLowerCase()
        }, [
            el('span', {
                'class': 'enum-index',
            }, index),
            el('span', {
                'class': 'enum-name',
            }, enumType.name)
        ])
        var comment = el('p', {
            'class': 'comment enum-comment route-description'
        }, enumType.comment)
        var rows = enumType.items.map(function (item, index) {
            return el('tr', null, [
                el('td', {'class': 'enum--item-index'}, index + 1),
                el('td', {'class': 'enum--item-name'}, el('code', null, item.name)),
                el('td', {'class': 'enum--item-value'}, item.value),
                el('td', {'class': 'comment enum--item-comment'}, item.comment)
            ])
        })
        rows.unshift(
            el('tr', null, [
                el('th', {'class': 'enum--header-index'}, '序号'),
                el('th', {'class': 'enum--header-name'}, '名称'),
                el('th', {'class': 'enum--header-value'}, '值'),
                el('th', {'class': 'enum--header-comment'}, '备注'),
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
            if (!renderEnums()) {
                enumList.html('<p class="is-empty">未注册枚举</p>')
            }
            rendered = true
        }
        enumPanel.css('display', 'flex')
    })

    $(document).on('click', 'code.arg-type.is-enum', function () {
        $('#btn-show-enums-panel').click()
        var target = '#enum-' + $(this).attr('data-type').toLowerCase()
        var item = $(target)
        if (!item.length) {
            return
        }
        setTimeout(function () {
            item.get(0).scrollIntoView()
            item.addClass('highlight')
            setTimeout(function () {
                item.removeClass('highlight')
            }, 1000)
        }, 200)
    })
})()