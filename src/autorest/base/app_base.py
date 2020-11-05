from werkzeug.exceptions import HTTPException
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Response

from ..base.app_context import AppContext
from ..base.request import HttpRequest
from ..routes.router import Router


class AppBase:
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

    def dispatch_request(self, request: HttpRequest):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            if endpoint == 'api_list':
                return self.router.api_list(request)

            if endpoint == 'entry_only':
                return self.router.route(request, values['entry'])

            if endpoint == 'entry_and_name':
                return self.router.route(request, values['entry'], values['name'])

            return Response(status=404)
        except HTTPException as e:
            return e

    def wsgi_app(self, environ, start_response):
        request = HttpRequest(environ, self.context)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        if not self.with_static:
            return self.wsgi_app(environ, start_response)

        if self.static_dir == '' or self.static_dir == '/':
            raise Exception('Invalid value of static dir: ' + self.static_dir)

        return SharedDataMiddleware(self.wsgi_app, {
            self.static_path: self.static_dir
        })(environ, start_response)
