from ...globs import current_app
from ...http import HttpResponse, NotFound
from ...middleware import MiddlewareBase
from ...routes.route_resolver import RouteResolver


class OptionsMiddleware(MiddlewareBase):
    """
    提供 options method 请求支持
    """

    # 可用的 method，即支持的 method 列表
    AVAILABLE_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']

    def __init__(self,
                 allow_origin=None,
                 allow_methods=None,
                 allow_headers=None,
                 allow_credentials=None,
                 max_age=None,
                 content_security_policy=None,
                 content_security_policy_report_only=None,
                 access_control_expose_headers=None,
                 cross_origin_opener_policy=None,
                 cross_origin_embedder_policy=None,
                 ):
        self.allow_origin = allow_origin
        self.allow_methods = allow_methods
        self.allow_headers = allow_headers
        self.allow_credentials = allow_credentials
        self.max_age = max_age
        self.content_security_policy = content_security_policy
        self.content_security_policy_report_only = content_security_policy_report_only
        self.access_control_expose_headers = access_control_expose_headers
        self.cross_origin_opener_policy = cross_origin_opener_policy
        self.cross_origin_embedder_policy = cross_origin_embedder_policy

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

        if self.content_security_policy is not None:
            response.content_security_policy = self.content_security_policy

        if self.content_security_policy_report_only is not None:
            response.content_security_policy_report_only = self.content_security_policy_report_only

        if self.access_control_expose_headers is not None:
            response.access_control_expose_headers = self.access_control_expose_headers

        if self.cross_origin_opener_policy is not None:
            response.cross_origin_opener_policy = self.cross_origin_opener_policy

        if self.cross_origin_embedder_policy is not None:
            response.cross_origin_embedder_policy = self.cross_origin_embedder_policy

        return response

    @classmethod
    def get_allow_methods(cls, request):
        app = current_app

        path = request.path
        entry = path[len('/' + app.api_prefix):]

        allow_methods = []

        if app.config.debug:
            # 调试模式时，从源码查找可用的路由
            entry = entry.lstrip('/')
            resolver = RouteResolver(
                app.config,
                app.router.entry_cache,
                request.method, entry
            )

            # 分别尝试不同 method 的路由是否存在
            for method in cls.AVAILABLE_METHODS:
                # 定义时，路由必须使用小写，所以处理成小写形式再去匹配
                if cls.has_method(resolver, method.lower()):
                    allow_methods.append(method)
        else:
            # 分别尝试不同 method 的路由是否存在
            for method in cls.AVAILABLE_METHODS:
                # 定义时，路由必须使用小写，所以处理成小写形式再去匹配
                rid = '%s#%s' % (entry, method.lower())
                if rid in app.router.production_routes:
                    allow_methods.append(method)

        return allow_methods

    @classmethod
    def has_method(cls, resolver, method: str):
        result = resolver.resolve(method)
        if not result:
            return False

        if isinstance(result, HttpResponse):
            return False

        return True
