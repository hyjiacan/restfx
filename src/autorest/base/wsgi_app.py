from werkzeug.exceptions import HTTPException
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Response

from ..base.app_context import AppContext
from ..base.request import HttpRequest
from ..routes.router import Router


class WsgiApp:
    def __init__(self,
                 context: AppContext,
                 api_prefix='api',
                 with_static=False,
                 static_dir='',
                 static_path='/static',
                 url_endswith_slash=False
                 ):
        self.context = context
        self.with_static = with_static
        self.api_prefix = api_prefix
        self.static_dir = static_dir
        self.static_path = static_path

        self.router = Router(self.context)

        self.url_map = Map([
            Rule('/%s%s' % (api_prefix, '/' if url_endswith_slash else ''), endpoint='api_list'),
            Rule('/%s/<entry>%s' % (api_prefix, '/' if url_endswith_slash else ''), endpoint='entry_only'),
            Rule('/%s/<entry>/<name>%s' % (api_prefix, '/' if url_endswith_slash else ''), endpoint='entry_and_name')
        ])

    def wsgi_app(self, environ, start_response):
        """
        接收并处理来自 wsgi 的请求
        :param environ:
        :param start_response:
        :return:
        """
        try:
            request = HttpRequest(environ, self.context)
            adapter = self.url_map.bind_to_environ(environ)

            endpoint, values = adapter.match()
            if endpoint == 'api_list':
                response = self.router.api_list(request)
            elif endpoint == 'entry_only':
                response = self.router.route(request, values['entry'])
            elif endpoint == 'entry_and_name':
                response = self.router.route(request, values['entry'], values['name'])
            else:
                response = Response(status=404)

            response.set_cookie(self.context.sessionid_name, request.session.id, path='/', httponly=True)

            return response(environ, start_response)
        except HTTPException as e:
            return e

    def __call__(self, environ, start_response):
        if not self.with_static:
            return self.wsgi_app(environ, start_response)

        if self.static_dir == '' or self.static_dir == '/':
            raise Exception('Invalid value of static dir: ' + self.static_dir)

        return SharedDataMiddleware(self.wsgi_app, {
            self.static_path: self.static_dir
        })(environ, start_response)
