from werkzeug import Request

from ..base.app_context import AppContext


class HttpRequest(Request):
    def __init__(self, environ, context: AppContext):
        super(HttpRequest, self).__init__(environ)
        self.context = context

        self.GET = self.args
        self.POST = self.form
        self.BODY = None
        self.FILES = self.files
