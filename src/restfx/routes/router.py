from types import FunctionType

from .route_resolver import RouteResolver
from ..context import AppContext
from ..http import HttpNotFound, HttpServerError, HttpResponse
from ..http.request import HttpRequest


class Router:
    def __init__(self, context: AppContext):
        self.context = context
        # 函数缓存，减少 inspect 反射调用次数
        self.entry_cache = {}
        """
        :type:Dict[str, Optional[FunctionDescription]]
        """
        # 线上模式时，使用固定路由
        self.production_routes = {}
        # 路由拦截器
        self.intercepter = None

    def dispatch(self, request: HttpRequest, entry):
        """
        路由分发入口
        :param request: 请求
        :param entry: 入口地址
        :return:
        """
        if self.intercepter is not None:
            # noinspection PyCallingNonCallable
            entry = self.intercepter(request, entry)

        if not self.context.debug:
            return self.route_for_production(request, '/' + entry)

        resolver = RouteResolver(self.context,
                                 self.entry_cache,
                                 request.method, entry)

        route = resolver.resolve()
        if isinstance(route, HttpResponse):
            return route

        return self.invoke_handler(request, route.func, route.arguments)

    def route_for_production(self, request, entry):
        method = request.method.lower()
        # noinspection PyBroadException
        try:
            route = self.production_routes['%s#%s' % (entry, method)]
        except Exception:
            return HttpNotFound()

        return self.invoke_handler(request, route['func'], route['args'])

    def invoke_handler(self, request, func: FunctionType, args):
        try:
            return func(request, args)
        except Exception as e:
            self.context.logger.error(e)
            return HttpServerError(repr(e))
