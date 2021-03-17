(function () {
  initPanel(optionPanel)

  document.querySelector('#btn-show-option-panel').addEventListener('click', function () {
    optionPanel.style.display = 'flex'
  })

  var selectType = document.querySelector('#option-select-type')
  var optionsSelectType = localStorage.getItem('options-select-type')
  if (!optionsSelectType) {
    optionsSelectType = '0'
  }
  selectType.value = optionsSelectType
  list.setAttribute('data-select-type', optionsSelectType)
  testPanel.setAttribute('data-select-type', optionsSelectType)
  selectType.addEventListener('change', function () {
    list.setAttribute('data-select-type', selectType.value)
    testPanel.setAttribute('data-select-type', selectType.value)
    localStorage.setItem('options-select-type', selectType.value)
  })
  document.querySelector('#tools').style.display = 'block'

  var expandedItem = document.querySelector('#expanded-on-load')
  expandedItem.addEventListener('change', function () {
    var val = expandedItem.checked
    localStorage.setItem('options-expanded', val ? '1' : '0')
  })

  var darkMode = document.querySelector('#dark-mode')
  var optionsDarkMode = localStorage.getItem('dark-mode')
  if (!optionsDarkMode) {
    optionsDarkMode = '0'
  }
  darkMode.checked = optionsDarkMode === '1'
  if (darkMode.checked) {
    document.body.classList.add('theme-dark')
  }
  darkMode.addEventListener('change', function () {
    var val = darkMode.checked
    if (val) {
      localStorage.setItem('dark-mode', '1')
      document.body.classList.add('theme-dark')
    } else {
      localStorage.setItem('dark-mode', '0')
      document.body.classList.remove('theme-dark')
    }

  })
})()
