import os
from types import FunctionType

from .route_resolver import RouteResolver
from ..context import AppContext
from ..http import HttpNotFound, HttpServerError, HttpResponse, JsonResponse
from ..http.request import HttpRequest
from ..util.func_util import FunctionDescription


class Router:
    def __init__(self, context: AppContext):
        self.context = context
        # 函数缓存，减少 inspect 反射调用次数
        self.entry_cache = {}
        """
        :type:Dict[str, Optional[FunctionDescription]]
        """
        # 开发模式的模块缓存，用于API列表
        self.routes_cache = {}
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
        if not self.context.enable_api_page:
            self.context.logger.info(
                'API list is disabled, '
                'use "App(..., enable_api_page=True, ...)" to enable it.')
            return HttpResponse(status=404)

        if not self.api_list_html_cache or not self.context.dev_options['api_page_cache']:
            with open(os.path.join(os.path.dirname(__file__),
                                   '../assets_for_dev/templates/api_list.html'),
                      encoding='utf-8') as fp:
                lines = fp.readlines()
                self.api_list_html_cache = ''.join(lines)
                fp.close()

        if request.method != 'POST':
            return HttpResponse(self.api_list_html_cache, content_type='text/html')

        if not self.routes_cache or not self.context.dev_options['api_page_cache']:
            routes = self.context.collector.collect(self.context.routes_map)

            if 'api_list_addition' in self.context.dev_options:
                addition_func = self.context.dev_options['api_list_addition']
            else:
                addition_func = None
            for route in routes:
                # 附加信息
                if addition_func is not None:
                    route['addition_info'] = addition_func(route)

            self.routes_cache = routes

        from restfx import __meta__
        return JsonResponse({
            'meta': {
                'name': __meta__.name,
                'version': __meta__.version
            },
            'app_name': self.context.dev_options['app_name'],
            'expanded': self.context.dev_options['api_list_expanded'],
            'routes': self.routes_cache,
        }, encoder=FunctionDescription.JSONEncoder)

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

        if not self.context.DEBUG:
            return self.route_for_production(request, '/' + entry)

        resolver = RouteResolver(self.context,
                                 self.routes_cache,
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
