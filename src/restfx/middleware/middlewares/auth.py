from ..interface import MiddlewareBase


class HttpAuthMiddleware(MiddlewareBase):
    def __init__(self, on_auth, auth_type='basic', realm='.'):
        self.on_auth = on_auth
        self.auth_type = auth_type
        self.realm = realm

    def process_request(self, request, meta):
        if self.on_auth(request, meta):
            return
        from restfx.http.response import HttpUnauthorized
        response = HttpUnauthorized()
        response.headers.set('WWW-Authenticate', '%s realm="%s"' % (self.auth_type, self.realm))
        return response
