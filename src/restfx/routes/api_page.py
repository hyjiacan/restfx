import os
from collections import OrderedDict

from ..context import AppContext
from ..http import HttpResponse, JsonResponse, HttpBadRequest
from ..util.func_util import FunctionDescription


class ApiPage:
    def __init__(self, context: AppContext):
        self.context = context
        # 开发模式的模块缓存，用于API列表
        self.routes_cache = {}
        # API列表页面缓存
        self.api_page_html_cache = ''

    def dispatch(self, request):
        if not self.context.api_page_options['api_page_enabled']:
            from ..util import Logger
            Logger.get(self.context.app_id).info(
                'API page is disabled, '
                'use "App(..., api_page_enabled=True, ...)" to enable it.')
            return HttpResponse(status=404)

        if request.method == 'GET':
            return self.do_get()

        if request.method == 'POST':
            if 'export' in request.GET and request.GET['export'] == 'md':
                return self.do_export(request)
            return self.do_post()

        return HttpResponse(status=405)

    def do_get(self):
        api_page_options = self.context.api_page_options
        if not self.api_page_html_cache or not api_page_options['api_page_cache']:
            with open(os.path.join(os.path.dirname(__file__),
                                   '../internal_assets/templates/api_page.html'),
                      encoding='utf-8') as fp:
                lines = fp.readlines()
                self.api_page_html_cache = ''.join(lines)
                fp.close()
        return HttpResponse(self.api_page_html_cache, content_type='text/html')

    def do_post(self):
        api_page_options = self.context.api_page_options
        if not self.routes_cache or not api_page_options['api_page_cache']:
            from . import Collector
            routes = Collector.get(self.context.app_id).collect(self.context.routes_map)
            addition_func = api_page_options.get('api_page_addition')

            for route in routes:
                # 附加信息
                if addition_func is not None:
                    route['addition_info'] = addition_func(route)

                # 移除参数上的其它信息 HttpRequest _xxx HttpSession
                raw_args = route['handler_info'].arguments
                new_args = OrderedDict()

                from ..http import HttpRequest
                from ..session import HttpSession

                for arg_name in raw_args:
                    arg = raw_args.get(arg_name)
                    if arg.is_injection:
                        continue
                    if arg.annotation == HttpRequest:
                        continue
                    if arg.annotation == HttpSession:
                        continue
                    new_args.setdefault(arg_name, arg)

                route['handler_info'].arguments = new_args

                # 移除 kwargs，以避免额外数据带来的数据传输消耗
                if 'kwargs' in route:
                    del route['kwargs']

            self.routes_cache = routes

        from restfx import __meta__
        return JsonResponse({
            'meta': {
                'name': __meta__.name,
                'version': __meta__.version,
                'url': __meta__.website
            },
            'name': api_page_options['api_page_name'],
            'expanded': api_page_options['api_page_expanded'],
            'routes': self.routes_cache,
        }, encoder=FunctionDescription.JSONEncoder)

    def do_export(self, request):
        if 'data' not in request.POST:
            return HttpBadRequest()

        content = request.POST['data']

        # noinspection PyBroadException
        try:
            from restfx.util import b64
            content = b64.dec_bytes(content)
        except Exception:
            # This exception can be ignored safety
            return HttpBadRequest()

        import time

        from restfx.http import FileResponse
        return FileResponse(content,
                            content_type='application/markdown;charset=utf8',
                            request=request,
                            attachment='%s[%s].md' % (
                                self.context.api_page_options['api_page_name'],
                                time.strftime('%Y%m%I%H%M%S'))
                            )
