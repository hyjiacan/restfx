import os

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
        if not self.context.api_page_enabled:
            self.context.logger.info(
                'API list is disabled, '
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
        if not self.api_page_html_cache or not self.context.api_page_options['api_page_cache']:
            with open(os.path.join(os.path.dirname(__file__),
                                   '../internal_assets/templates/apipage.html'),
                      encoding='utf-8') as fp:
                lines = fp.readlines()
                self.api_page_html_cache = ''.join(lines)
                fp.close()
        return HttpResponse(self.api_page_html_cache, content_type='text/html')

    def do_post(self):
        if not self.routes_cache or not self.context.api_page_options['api_page_cache']:
            routes = self.context.collector.collect(self.context.routes_map)

            if 'api_page_addition' in self.context.api_page_options:
                addition_func = self.context.api_page_options['api_page_addition']
            else:
                addition_func = None
            for route in routes:
                # 附加信息
                if addition_func is not None:
                    route['addition_info'] = addition_func(route)
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
            'name': self.context.api_page_options['api_page_name'],
            'expanded': self.context.api_page_options['api_page_expanded'],
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

        import urllib.parse
        import time

        return HttpResponse(content, content_type='application/markdown;charset=utf8', headers={
            'Content-Disposition': 'attachment;filename=%s_%s.md' % (
                urllib.parse.quote(self.context.api_page_options['api_page_name']),
                time.strftime('%Y-%m-%I_%H_%M_%S')
            )
        })
