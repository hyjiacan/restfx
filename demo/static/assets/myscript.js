restfx.on('request', function(method, url, option) {
    return option
})

restfx.on('response', function(method, url, response) {
    if(response.status === 400) {
        response.statusText = 'Oops! ' + response.statusText
    }
    return response
})

const origin = window.location.origin

fetch(origin + '/api/test/sse', {
  method: 'GET',
  headers: {
    'Accept': 'text/event-stream',
  },
})
  .then(response => {
    if (!response.ok) {
      throw new Error('HTTP 请求失败');
    }

    const eventSource = new EventSource(response.url);
    eventSource.onmessage = event => {
      console.log(event.data);
    };
  })
  .catch(error => {
    console.error(error.message);
  });