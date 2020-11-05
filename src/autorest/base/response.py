import json

from werkzeug.wrappers import Response


class HttpResponse(Response):
    def __init__(self, content=None, content_type='text/html', status=200, **kwargs):
        super(Response, self).__init__(content, content_type=content_type, status=status, **kwargs)


class JsonResponse(HttpResponse):
    def __init__(self, obj, encoder=None):
        content = json.dumps(obj, cls=encoder)
        super(HttpResponse, self).__init__(content, content_type='application/json')


class HttpResponseBadRequest(HttpResponse):
    def __init__(self, content=None):
        super(HttpResponse, self).__init__(content, status=400)


class HttpResponseNotFound(HttpResponse):
    def __init__(self, content=None):
        super(HttpResponse, self).__init__(content, status=404)


class HttpResponseServerError(HttpResponse):
    def __init__(self, content=None):
        if isinstance(content, Exception):
            content = repr(content)
        super(HttpResponse, self).__init__(content, status=500)
