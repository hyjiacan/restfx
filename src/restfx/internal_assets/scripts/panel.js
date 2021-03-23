function toggleFullscreen(panel) {
  panel = $('.panel', panel)
  panel.toggleClass('fullscreen')
}

function initPanel(panel) {
  $('.btn-close', panel).on('click', function () {
    panel.hide()
    return false
  })
  $('.btn-fullscreen', panel).on('click', function () {
    toggleFullscreen(panel)
    return false
  })

  var lastClick = 0
  $('.panel-heading', panel).on('click', function (e) {
    var now = new Date()
    if (now - lastClick > 200) {
      lastClick = now
      return
    }
    toggleFullscreen(panel)
  })
}
