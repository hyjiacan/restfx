from ...globs import current_app
from ...http import HttpResponse, NotFound
from ...middleware import MiddlewareBase
from ...routes.route_resolver import RouteResolver


class OptionsMiddleware(MiddlewareBase):
    """
    提供 options method 请求支持
    """

    def __init__(self, allow_origin=None, allow_methods=None, allow_headers=None, allow_credentials=None, max_age=None):
        self.allow_origin = allow_origin
        self.allow_methods = allow_methods
        self.allow_headers = allow_headers
        self.allow_credentials = allow_credentials
        self.max_age = max_age

    def on_coming(self, request):
        if request.method != 'OPTIONS':
            return

        allow_methods = self.allow_methods or self.get_allow_methods(request)
        if not allow_methods:
            return NotFound()

        response = HttpResponse()
        response.access_control_allow_methods = allow_methods

        if self.allow_origin is not None:
            response.access_control_allow_origin = self.allow_origin

        if self.allow_credentials is not None:
            response.access_control_allow_credentials = self.allow_credentials

        if self.allow_headers is not None:
            response.access_control_allow_headers = self.allow_headers

        if self.max_age is not None:
            response.access_control_max_age = self.max_age

        return response

    @classmethod
    def get_allow_methods(cls, request):
        app = current_app

        entry = request.path[len('/' + app._api_prefix):].lstrip('/')

        resolver = RouteResolver(
            app.config,
            app._router.entry_cache,
            request.method, entry
        )

        allow_methods = []

        if cls.has_method(resolver, 'get'):
            allow_methods.append('GET')
        if cls.has_method(resolver, 'post'):
            allow_methods.append('POST')
        if cls.has_method(resolver, 'put'):
            allow_methods.append('PUT')
        if cls.has_method(resolver, 'delete'):
            allow_methods.append('DELETE')
        if cls.has_method(resolver, 'patch'):
            allow_methods.append('PATCH')

        return allow_methods

    @classmethod
    def has_method(cls, resolver, method: str):
        result = resolver.resolve(method)
        if not result:
            return False

        if isinstance(result, HttpResponse):
            return False

        return True
