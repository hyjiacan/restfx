import json

from werkzeug.exceptions import InternalServerError
from werkzeug.utils import escape
from werkzeug.wrappers import Response


class HttpResponse(Response):
    def __init__(self, content=None, content_type='text/html;charset=utf8', status=200, headers=None, **kwargs):
        super().__init__(content, content_type=content_type, status=status, headers=headers, **kwargs)


class JsonResponse(HttpResponse):
    def __init__(self, obj, encoder=None, content_type='application/json;charset=utf8', ensure_ascii=True, **kwargs):
        content = json.dumps(obj, ensure_ascii=ensure_ascii, cls=encoder)
        super().__init__(content, content_type=content_type, **kwargs)


class FileResponse(HttpResponse):
    def __init__(self, fp, **kwargs):
        # 如果是字符串，就认为是文件路径
        if isinstance(fp, str):
            self.fp = open(fp, mode='rb')
        else:
            self.fp = fp
        super().__init__(self.fp, direct_passthrough=True, **kwargs)


class HttpBadRequest(HttpResponse):
    def __init__(self, content=None, **kwargs):
        super().__init__(content, status=400, **kwargs)


class HttpRedirect(HttpResponse):
    def __init__(self, location, status=302, **kwargs):
        super().__init__(None, status=status, headers={
            'Location': escape(location)
        }, **kwargs)


class HttpUnauthorized(HttpResponse):
    def __init__(self, content=None, **kwargs):
        super().__init__(content, status=401, **kwargs)


class HttpNotFound(HttpResponse):
    def __init__(self, content=None, **kwargs):
        super().__init__(content, status=404, **kwargs)


class HttpServerError(HttpResponse, InternalServerError):
    def __init__(self, content=None, **kwargs):
        e = None
        if isinstance(content, Exception):
            e = content
            content = None
        super().__init__(content, None, e, **kwargs)
