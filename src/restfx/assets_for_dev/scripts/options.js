(function() {
  initPanel(optionPanel)

  document.querySelector('#btn-show-option-panel').addEventListener('click', function() {
    optionPanel.style.display = 'flex'
  })

  var selectType = document.querySelector('#option-select-type')
  var optionsSelectType = localStorage.getItem('options-select-type')
  if(!optionsSelectType) {
    optionsSelectType = '0'
  }
  selectType.value = optionsSelectType
  list.setAttribute('data-select-type',  optionsSelectType)
  testPanel.setAttribute('data-select-type',  optionsSelectType)
  selectType.addEventListener('change',  function() {
    list.setAttribute('data-select-type',  selectType.value)
    testPanel.setAttribute('data-select-type',  selectType.value)
    localStorage.setItem('options-select-type', selectType.value)
  })
  document.querySelector('#tools').style.display = 'block'

  var expandedItem = document.querySelector('#expanded-on-load')
  expandedItem.addEventListener('change',  function() {
    var val  = expandedItem.checked
    localStorage.setItem('options-expanded', val ? '1' : '0')
  })
})()