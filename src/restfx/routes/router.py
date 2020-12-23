import os
from types import FunctionType

from .route_resolver import RouteResolver
from ..app_context import AppContext
from ..http import HttpNotFound, HttpServerError, HttpResponse, JsonResponse
from ..http.request import HttpRequest
from ..util.func_util import FunctionDescription
from ..util.utils import get_func_info


class Router:
    def __init__(self, context: AppContext):
        self.context = context
        # 函数缓存，减少 inspect 反射调用次数
        self.entry_cache = {}
        """
        :type:Dict[str, Optional[FunctionDescription]]
        """
        # 开发模式的模块缓存，用于API列表
        self.modules_cache = {}
        # 线上模式时，使用固定路由
        self.production_routes = {}
        # API列表页面缓存
        self.api_list_html_cache = ''
        # 路由拦截器
        self.intercepter = None

    def api_list(self, request):
        """
        渲染 API 列表
        :param request:
        :return:
        """
        if not self.context.DEBUG:
            self.context.logger.info(
                'API list is disabled in production, use "App(..., debug_mode=True, ...)" to enable it.')
            return HttpResponse(status=404)

        if not self.api_list_html_cache:
            with open(os.path.join(os.path.dirname(__file__), '../assets_for_dev/templates/api_list.html'),
                      encoding='utf-8') as fp:
                lines = fp.readlines()
                self.api_list_html_cache = ''.join(lines)
                fp.close()

        if request.method != 'POST':
            return HttpResponse(self.api_list_html_cache, content_type='text/html')

        if not self.modules_cache:
            routes = self.context.collector.collect(self.context.routes_map)

            modules = {}

            for route in routes:
                module = route['module']

                if module in modules:
                    modules[module].append(route)
                else:
                    modules[module] = [route]
            self.modules_cache = modules

        return JsonResponse(self.modules_cache, encoder=FunctionDescription.JSONEncoder)

    def dispatch(self, request: HttpRequest, entry):
        """
        路由分发入口
        :param request: 请求
        :param entry: 入口文件，包名使用 . 符号分隔
        :return:
        """
        if self.intercepter is not None:
            # noinspection PyCallingNonCallable
            entry = self.intercepter(request, entry)

        if not self.context.DEBUG:
            return self.route_for_production(request, entry)

        resolver = RouteResolver(self.context,
                                 self.modules_cache,
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
            message = '\t%s' % get_func_info(func)
            self.context.logger.error(message, e)
            return HttpServerError('%s: %s' % (message, str(e)))
