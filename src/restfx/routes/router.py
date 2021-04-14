from types import FunctionType

from .route_resolver import RouteResolver
from ..config import AppConfig
from ..http import HttpNotFound, HttpResponse
from ..http.request import HttpRequest


class Router:
    def __init__(self, config: AppConfig):
        self.config = config
        # 函数缓存，减少 inspect 反射调用次数
        self.entry_cache = {}
        """
        :type:Dict[str, Optional[FunctionDescription]]
        """
        # 线上模式时，使用固定路由
        self.production_routes = {}

    def dispatch(self, request: HttpRequest, entry):
        """
        路由分发入口
        :param request: 请求
        :param entry: 入口地址
        :return:
        """
        if not self.config.debug:
            return self.route_for_production(request, '/' + entry)

        resolver = RouteResolver(self.config,
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
            from ..util import Logger, func_util
            Logger.get(self.config.app_id).error(func_util.get_func_info(func), e)
