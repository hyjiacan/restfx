import uuid
from werkzeug import Request
from werkzeug.datastructures import ImmutableDict, ImmutableMultiDict, FileStorage

from restfx.util import ContextStore
from restfx.globals import _request_ctx_stack, _app_ctx_stack


def _get_request_data(data: ImmutableMultiDict) -> ImmutableDict:
    args = {}
    for key in data.keys():
        value = data.getlist(key)
        value_len = len(value)
        if not value_len:
            args[key] = None
            continue
        if value_len == 1:
            args[key] = value[0]
            continue
        args[key] = value
    return ImmutableDict(args)


class RequestContext:
    def __init__(self, request):
        self.request = request
        self.store = ContextStore(_request_ctx_stack)
        self.ref_count = 0

    @property
    def session(self):
        return self.request.session

    def push(self):
        top = _app_ctx_stack.top
        if not top or top != self.request.app:
            self.request.app.context.push()
        if _request_ctx_stack.top != self:
            _request_ctx_stack.push(self)
        self.ref_count += 1

    def pop(self):
        if _request_ctx_stack.top != self:
            return
        self.ref_count -= 1
        if self.ref_count > 0:
            return
        _request_ctx_stack.pop()
        del self.store

    def __enter__(self):
        self.push()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pop()


class HttpRequest(Request):
    def __init__(self, environ, app):
        super().__init__(environ)
        self.id = str(uuid.uuid4())
        self.app = app
        self.app_id = app.id
        self.GET = _get_request_data(self.args)
        self.POST = _get_request_data(self.form)
        self.BODY = self.data
        self.FILES = self.files
        self.COOKIES = self.cookies
        self.session = None
        self.injections = {}
        # 在同一个请求中，使用同一个请求上下文
        self._ctx = RequestContext(self)

    def inject(self, **kwargs):
        self.injections.update(kwargs)

    def context(self, **kwargs):
        self._ctx.store.update(kwargs)
        return self._ctx


class HttpFile(FileStorage):
    pass
