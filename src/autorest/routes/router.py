import os

from .path_resolver import PathResolver
from ..base.app_context import AppContext
from ..base.request import HttpRequest
from ..base.response import HttpResponseNotFound, HttpResponseServerError, HttpResponse, JsonResponse
from ..util.func_util import ArgumentSpecification
from ..util.utils import get_func_info


class Router:
    def __init__(self, context: AppContext):
        self.context = context
        # 函数缓存，减少 inspect 反射调用次数
        self.entry_cache = {}
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
            return HttpResponse(status=404)

        if not self.api_list_html_cache:
            with open(os.path.join(os.path.dirname(__file__), '../templates/api_list.html'), encoding='utf-8') as fp:
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

                # 移除路径两侧的 / 符号
                p = route['path'].strip('/')
                suffix = ''
                temp = p.split('/')
                entry = temp[0]
                if len(temp) == 2:
                    suffix = temp[1]

                resolver = PathResolver(self.context,
                                        self.modules_cache,
                                        self.entry_cache,
                                        route['method'], entry, suffix)
                resolver.check()
                define = resolver.get_func_define()

                if isinstance(define, HttpResponse):
                    continue

                if define and len(define['args']) > 0:
                    route['args'] = [define['args'][arg] for arg in define['args']]
                else:
                    route['args'] = None

                # 不需要 kwargs ，因为其中的数据是无法预估的，在api列表中也没有多大的意义
                if 'kwargs' in route:
                    del route['kwargs']

                if module in modules:
                    modules[module].append(route)
                else:
                    modules[module] = [route]
            self.modules_cache = modules

        return JsonResponse(self.modules_cache, encoder=ArgumentSpecification.JsonEncoder)

    def route(self, request: HttpRequest, entry, name=''):
        """
        路由分发入口
        :param request: 请求
        :param entry: 入口文件，包名使用 . 符号分隔
        :param name='' 指定的函数名称
        :return:
        """
        if self.intercepter is not None:
            # noinspection PyCallingNonCallable
            entry, name = self.intercepter(request, entry, name)

        if not self.context.DEBUG:
            return self.route_for_production(request, entry, name)

        resolver = PathResolver(self.context,
                                self.modules_cache,
                                self.entry_cache,
                                request.method, entry, name)
        check_result = resolver.check()
        if isinstance(check_result, HttpResponse):
            return check_result
        func_define = resolver.resolve()
        if isinstance(func_define, HttpResponse):
            return func_define

        return self.invoke_handler(request, func_define['func'], func_define['args'])

    def route_for_production(self, request, entry, name):
        method = request.method.lower()
        # noinspection PyBroadException
        try:
            if name == '':
                route = self.production_routes['%s#%s' % (entry, method)]
            else:
                route = self.production_routes['%s/%s#%s' % (entry, name, method)]
        except Exception:
            return HttpResponseNotFound()

        return self.invoke_handler(request, route['func'], route['args'])

    def invoke_handler(self, request, func, args):
        try:
            return func(request, args)
        except Exception as e:
            message = '\t%s' % get_func_info(func)
            self.context.logger.error(message, e)
            return HttpResponseServerError('%s: %s' % (message, str(e)))
