from werkzeug import Request

from ..base.app_context import AppContext


class HttpRequest(Request):
    def __init__(self, environ, context: AppContext):
        super(HttpRequest, self).__init__(environ)
        self.context = context

        self.B = {}
        self.G = {}
        self.P = {}
