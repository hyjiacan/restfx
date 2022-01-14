import json
import os
import uuid

# from admin_plugin.plugin import AdminPlugin

from midlewares import MiddlewareA
from restfx import App
from restfx.http import HttpRequest, HttpResponse
from restfx.http.response import Redirect
from restfx.middleware.access import AccessMiddleware
from restfx.middleware.middlewares import HttpAuthMiddleware, SessionMiddleware, TimetickMiddleware
from restfx.middleware.middlewares import OptionsMiddleware
from restfx.routes import RouteMeta
from restfx.session.providers import RedisSessionProvider, MemorySessionProvider
from test.tools.enums import OpTypes

root = os.path.dirname(__file__)


def test_id(request: HttpRequest, **kwargs):
    return HttpResponse(json.dumps(kwargs))


DEBUG_MODE = True

app_id = '82615610-3aa5-491e-aa58-fab3a9561e64'


def api_page_addition(route):
    if route['kwargs'].get('auth', True):
        return '<span style="color: #ff7d7d">[需要身份校验]</span>'
    return '<span style="color: #66c0de">[不需要身份校验]</span>'


api_page_assets = (
    '/assets/myscript.js',
    '/assets/mystyle.css'
)

app = App(root,
          app_id=app_id,
          debug=DEBUG_MODE,
          api_page_name='restfx 测试项目',
          api_page_addition=api_page_addition,
          api_page_assets=api_page_assets,
          api_page_expanded=True
          )

app.map_routes({
    'test': 'test.api'
}).map_static({
    '/': 'static'
}).map_urls({
    '/': lambda request: Redirect('/index.html'),
    '/test/<param>': lambda request, param: HttpResponse(param)
})

app.register_types(OpTypes)


def on_auth(request: HttpRequest, meta: RouteMeta):
    # 不需要授权
    if not meta.get('auth', True):
        return True
    if request.authorization is None:
        return False
    if request.authorization.username == 'aaa' and request.authorization.password == 'bbb':
        return True
    else:
        return False


def sessionid_maker(request):
    return uuid.uuid4().hex


app.register_middleware(
    AccessMiddleware(),
    TimetickMiddleware(),
    OptionsMiddleware(),
    HttpAuthMiddleware(on_auth),
    SessionMiddleware(MemorySessionProvider()),
    # SessionMiddleware(MySQLSessionProvider(db_options={
    #     'host': '127.0.0.1',
    #     'port': 3306,
    #     'user': 'root',
    #     'password': '',
    #     'database': 'test',
    #     'charset': 'utf8',
    # }), maker=sessionid_maker),
    # SessionMiddleware(RedisSessionProvider({
    #     'host': '172.16.51.17',
    #     'password': '123asd!@#$',
    #     'db': 15
    # }), maker=sessionid_maker),
    MiddlewareA(),
    # MiddlewareB(),
    # MiddlewareC()
)
app.inject(injection='try1try')


def load_routes_map():
    app.persist('dest/routes.py')
    from dest import routes
    app.register_routes(routes.routes)


def command_persist():
    import sys
    if len(sys.argv) < 2:
        return False

    arg1 = sys.argv[1]
    if arg1 != 'persist':
        return False

    app.persist()
    return True


if __name__ == '__main__':
    # 提供对 python main.py persist 命令的支持
    if command_persist():
        exit(0)
    else:
        # app.register_plugins(AdminPlugin())
        load_routes_map()
        # 启动内置服务器
        app.startup()
