import os

from ..config import AppConfig
from ..http import BadRequest, HttpResponse, JsonResponse, NotFound
from ..util import utils
from ..util.func_util import FunctionDescription


class ApiPage:
    def __init__(self, config: AppConfig):
        self.config = config
        # 开发模式的模块缓存，用于API列表
        self.routes_cache = {}
        # API列表页面缓存
        self.api_page_html_cache = ''

        self.prefix = '/%s%s' % (config.api_prefix, '/' if config.append_slash else '')

    def dispatch(self, request):
        if not self.config.api_page_enabled:
            from ..util import Logger
            Logger.current().info(
                'API page is disabled, '
                'use "App(..., api_page_enabled=True, ...)" to enable it.')
            return NotFound()

        prefix = self.prefix

        if request.path.lower() == prefix:
            return self.render_page(request)

        if not prefix.endswith('/'):
            prefix += '/'

        if request.path.lower() == prefix + 'export':
            return self.do_export(request)

        if request.path.lower() == prefix + 'api.json':
            return self.return_api_info(request)

        return NotFound()

    def render_page(self, request):
        if request.method != 'GET':
            return NotFound()
        if not self.api_page_html_cache or not self.config.api_page_cache:
            from .. import __meta__
            with open(os.path.join(os.path.dirname(__file__),
                                   '../internal_assets/templates/api_page.html'),
                      encoding='utf-8') as fp:
                lines = [
                    line.replace('{{version}}', __meta__.version)
                    for line in fp.readlines()
                ]
                self.api_page_html_cache = ''.join(lines)
                fp.close()
        return HttpResponse(self.api_page_html_cache, content_type='text/html')

    def return_api_info(self, request):
        if not self.routes_cache or not self.config.api_page_cache:
            self.routes_cache = self.config.docs

        from .. import __meta__
        return JsonResponse({
            'api_version': __meta__.api_version,
            'meta': {
                'name': __meta__.name,
                'version': __meta__.version,
                'url': __meta__.website
            },
            'name': self.config.api_page_name,
            'expanded': self.config.api_page_expanded,
            'routes': self.routes_cache,
            'enums': [
                utils.get_enum_items(item)
                for item in self.config.enum_types
            ],
            'custom_assets': self.config.api_page_assets
        }, encoder=FunctionDescription.JSONEncoder, ensure_ascii=request.GET.get('ascii') == 'true')

    def do_export(self, request):
        if request.method != 'POST':
            return NotFound()

        if 'data' not in request.POST:
            return BadRequest()

        content = request.POST['data']

        # noinspection PyBroadException
        try:
            from ..util import b64
            content = b64.dec_bytes(content)
        except Exception:
            # This exception can be ignored safety
            return BadRequest()

        import time

        from ..http import FileResponse
        return FileResponse(content,
                            content_type='application/markdown;charset=utf-8',
                            request=request,
                            attachment='%s[%s].md' % (
                                self.config.api_page_name,
                                time.strftime('%Y%m%I%H%M%S'))
                            )
