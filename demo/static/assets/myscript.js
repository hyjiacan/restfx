restfx.on('request', function(method, url, option) {
    return option
})

restfx.on('response', function(method, url, response) {
    if(response.status === 400) {
        response.statusText = 'Oops! ' + response.statusText
    }
    return response
})