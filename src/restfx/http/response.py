import json

from werkzeug.exceptions import InternalServerError
from werkzeug.wrappers import Response


class HttpResponse(Response):
    def __init__(self, content=None, content_type='text/html;charset=utf8', status=200, headers=None, **kwargs):
        super().__init__(content, content_type=content_type, status=status, headers=headers, **kwargs)


class JsonResponse(HttpResponse):
    def __init__(self, obj, encoder=None):
        content = json.dumps(obj, ensure_ascii=True, cls=encoder)
        super().__init__(content, content_type='application/json;charset=utf8')


class HttpBadRequest(HttpResponse):
    def __init__(self, content=None):
        super().__init__(content, status=400)


class HttpUnauthorized(HttpResponse):
    def __init__(self, content=None):
        super().__init__(content, status=401)


class HttpNotFound(HttpResponse):
    def __init__(self, content=None):
        super().__init__(content, status=404)


class HttpServerError(InternalServerError, HttpResponse):
    def __init__(self, content=None):
        e = None
        if isinstance(content, Exception):
            e = content
            content = None
        super().__init__(content, None, e)
