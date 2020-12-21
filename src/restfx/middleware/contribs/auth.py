from .. import MiddlewareBase
from ...routes import RouteMeta


class HttpAuthMiddleware(MiddlewareBase):
    def __int__(self):
        self.auth_type = 'basic'
        self.realm = '.'
        self.on_auth = None

    def process_request(self, request, meta: RouteMeta, **kwargs):
        if self.on_auth(request, meta):
            return
        from restfx.http.response import HttpUnauthorized
        response = HttpUnauthorized()
        response.headers.set('WWW-Authenticate', '%s realm="%s"' % (self.auth_type, self.realm))
        return response

    def process_invoke(self, request, meta: RouteMeta, **kwargs):
        pass

    def process_return(self, request, meta: RouteMeta, **kwargs):
        pass

    def process_response(self, request, meta: RouteMeta, **kwargs):
        pass
