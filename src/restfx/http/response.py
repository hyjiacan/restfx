import json

from werkzeug.exceptions import BadRequest, NotFound, InternalServerError
from werkzeug.wrappers import Response


class HttpResponse(Response):
    def __init__(self, content=None, content_type='text/html', status=200, headers=None, **kwargs):
        super().__init__(content, content_type=content_type, status=status, headers=headers, **kwargs)


class JsonResponse(HttpResponse):
    def __init__(self, obj, encoder=None):
        content = json.dumps(obj, cls=encoder)
        super().__init__(content, content_type='application/json')


class HttpResponseBadRequest(BadRequest, HttpResponse):
    def __init__(self, content=None):
        super().__init__(content)


class HttpResponseNotFound(NotFound, HttpResponse):
    def __init__(self, content=None):
        super().__init__(content)


class HttpResponseServerError(InternalServerError, HttpResponse):
    def __init__(self, content=None):
        if isinstance(content, Exception):
            content = repr(content)
        super().__init__(content)
