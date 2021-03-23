(function () {
  initPanel(optionPanel)

  $('#btn-show-option-panel').on('click', function () {
    optionPanel.css('display', 'flex')
  })

  var selectType = $('#option-select-type')
  var optionsSelectType = localStorage.getItem('options-select-type')
  if (!optionsSelectType) {
    optionsSelectType = '0'
  }
  selectType.val(optionsSelectType)
  list.attr('data-select-type', optionsSelectType)
  testPanel.attr('data-select-type', optionsSelectType)
  selectType.on('change', function () {
    list.attr('data-select-type', selectType.val())
    testPanel.attr('data-select-type', selectType.val())
    localStorage.setItem('options-select-type', selectType.val())
  })
  $('#tools').show()

  var expandedItem = $('#expanded-on-load')
  expandedItem.on('change', function () {
    var val = expandedItem.is(':checked')
    localStorage.setItem('options-expanded', val ? '1' : '0')
  })

  var darkMode = $('#dark-mode')
  var optionsDarkMode = localStorage.getItem('dark-mode')
  if (!optionsDarkMode) {
    optionsDarkMode = '0'
  }
  darkMode.prop('checked', optionsDarkMode === '1')
  if (darkMode.is(':checked')) {
    document.body.classList.add('theme-dark')
  }
  darkMode.on('change', function () {
    var val = darkMode.is(':checked')
    if (val) {
      localStorage.setItem('dark-mode', '1')
      document.body.classList.add('theme-dark')
    } else {
      localStorage.setItem('dark-mode', '0')
      document.body.classList.remove('theme-dark')
    }
  })
})()
