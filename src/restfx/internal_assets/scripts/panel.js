function toggleFullscreen(panel) {
  panel = panel.querySelector('.panel')
  if (panel.classList.contains('fullscreen')) {
    panel.classList.remove('fullscreen')
  } else {
    panel.classList.add('fullscreen')
  }
}

function initPanel(panel) {
  panel.querySelector('.btn-close').addEventListener('click', function () {
    panel.style.display = 'none'
    return false
  })

  panel.querySelector('.btn-fullscreen').addEventListener('click', function() {
    toggleFullscreen(panel)
    return false
  })

  var lastClick = 0
  panel.querySelector('.panel-heading').addEventListener('click', function (e) {
    var now = new Date()
    if (now - lastClick > 200) {
      lastClick = now
      return
    }
    toggleFullscreen(panel)
  })
}