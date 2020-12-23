import os

from werkzeug.exceptions import NotFound
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Response

from .app_context import AppContext
from .http import HttpRequest, HttpServerError, HttpNotFound
from .routes.router import Router


class WsgiApp:
    def __init__(self,
                 context: AppContext,
                 api_prefix='api',
                 static_map: dict = None,
                 url_endswith_slash=False
                 ):
        self.context = context
        self.api_prefix = api_prefix
        self.router = Router(self.context)

        if static_map is None:
            static_map = {}
        else:
            for url in static_map:
                target_path = static_map[url]
                abs_target_path = os.path.abspath(os.path.join(context.ROOT, target_path))
                static_map[url] = abs_target_path
                if os.path.exists(abs_target_path):
                    self.context.logger.debug('Map static url %s to path %s' % (url, abs_target_path))
                else:
                    self.context.logger.warning(
                        'The target path of static url %s not found: %s' % (url, abs_target_path))

        if context.DEBUG:
            static_map['/restfx_assets_for_dev'] = os.path.join(os.path.dirname(__file__), 'assets_for_dev')
        self.static_map = static_map

        self.url_map = Map([
            Rule('/%s%s' % (api_prefix, '/' if url_endswith_slash else ''), endpoint='api_list'),
            Rule('/%s/<path:entry>%s' % (api_prefix, '/' if url_endswith_slash else ''), endpoint='entry_only')
        ])

    def wsgi_app(self, environ, start_response):
        """
        接收并处理来自 wsgi 的请求
        :param environ:
        :param start_response:
        :return:
        """
        request = None
        try:
            request = HttpRequest(environ, self.context.app_id)
            adapter = self.url_map.bind_to_environ(environ)

            # 仅在调试时重定向
            if self.context.DEBUG and request.path == '/':
                response = Response(status=302, headers={
                    'Location': '/' + self.api_prefix
                })
            else:
                endpoint, values = adapter.match()
                if endpoint == 'api_list':
                    response = self.router.api_list(request)
                elif endpoint == 'entry_only':
                    response = self.router.dispatch(request, values['entry'])
                else:
                    response = Response(status=404)
        except Exception as e:
            if isinstance(e, NotFound):
                response = HttpNotFound()
            elif self.context.DEBUG:
                raise e
            else:
                response = HttpServerError()

            msg = repr(e)
            if request:
                msg += ':' + request.path
            self.context.logger.warning(msg)

        return response(environ, start_response)

    def __call__(self, environ, start_response):
        if not self.static_map:
            return self.wsgi_app(environ, start_response)

        return SharedDataMiddleware(self.wsgi_app, self.static_map)(environ, start_response)

    def close(self):
        self.context.session_provider.dispose()
