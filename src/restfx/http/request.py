import uuid
from functools import partial

from werkzeug import Request
from werkzeug.local import LocalProxy
from werkzeug.local import LocalStack
from werkzeug.datastructures import ImmutableDict, ImmutableMultiDict, FileStorage

from restfx.util import ContextStore


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


_request_ctx_err_msg = """\
Working outside of request context.

This typically means that you attempted to use functionality that needed
an active HTTP request.  Consult the documentation on testing for
information about how to avoid this problem.\
"""


def _lookup_req_object(name):
    top = _request_ctx_stack.top
    if top is None:
        raise RuntimeError(_request_ctx_err_msg)
    return getattr(top, name)


_request_ctx_stack = LocalStack()
current_request = LocalProxy(partial(_lookup_req_object, 'request'))
current_store = LocalProxy(partial(_lookup_req_object, 'store'))


class RequestContext:
    def __init__(self, request):
        self.request = request
        self.store = ContextStore(_request_ctx_stack)

    @property
    def session(self):
        return self.request.session

    def __enter__(self):
        _request_ctx_stack.push(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        _request_ctx_stack.pop()
        del self.store


class HttpRequest(Request):
    def __init__(self, environ, app_id: str):
        super().__init__(environ)
        self.id = str(uuid.uuid4())
        self.app_id = app_id
        self.GET = _get_request_data(self.args)
        self.POST = _get_request_data(self.form)
        self.BODY = self.data
        self.FILES = self.files
        self.COOKIES = self.cookies
        self.session = None
        self.injections = {}

    def inject(self, **kwargs):
        self.injections.update(kwargs)

    def context(self, **kwargs):
        ctx = RequestContext(self)
        ctx.store.update(kwargs)
        return ctx


class HttpFile(FileStorage):
    pass
