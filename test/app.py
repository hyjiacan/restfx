import json
import os
import uuid

import pymysql

from midlewares import MiddlewareA
from restfx import App
from restfx.http import HttpRequest, HttpResponse
from restfx.http.response import HttpRedirect
from restfx.middleware.middlewares import HttpAuthMiddleware, SessionMiddleware
from restfx.middleware.middlewares.timetick import TimetickMiddleware
from restfx.routes import RouteMeta
from restfx.session.providers import MemorySessionProvider, MySQLSessionProvider
from test.tools.enums import OpTypes

root = os.path.dirname(__file__)

session_provider = MySQLSessionProvider(pool_options={
    'creator': pymysql,
    'host': '172.16.53.3',
    'port': 3306,
    'user': 'root',
    'password': '123asd!@#',
    'database': 'test',
    'charset': 'utf8',
})


def test_id(request: HttpRequest, **kwargs):
    return HttpResponse(json.dumps(kwargs))


DEBUG_MODE = True

app_id = '82615610-3aa5-491e-aa58-fab3a9561e64'


def api_page_addition(route):
    if route['kwargs'].get('auth', True):
        return '<span style="color: #ff7d7d">[需要身份校验]</span>'
    return '<span style="color: #66c0de">[不需要身份校验]</span>'


app = App(root,
          app_id=app_id,
          debug=DEBUG_MODE,
          api_page_name='restfx 测试项目',
          api_page_addition=api_page_addition,
          api_page_expanded=True)

app.map_routes({
    'test': 'test.api'
}).map_static({
    '/': 'static'
}).map_urls({
    '/': lambda request: HttpRedirect('/index.html'),
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


def sessionid_maker(request, app_id):
    return uuid.uuid4().hex


app.register_middleware(
    TimetickMiddleware(),
    HttpAuthMiddleware(on_auth),
    SessionMiddleware(MemorySessionProvider(20)),
    # SessionMiddleware(session_provider, sessid_maker=sessionid_maker),
    MiddlewareA(),
    # MiddlewareB(),
    # MiddlewareC()
)
app.inject(injection='try1try')


def on_requesting(e):
    print('requesting')


def on_requested(e):
    print('requested')


app.on('requesting', on_requesting)
app.on('requested', on_requested)


def load_routes_map():
    import routes_map
    app.register_routes(routes_map.routes)


def command_persist():
    import sys
    if len(sys.argv) < 2:
        return False

    arg1 = sys.argv[1]
    if arg1 != 'persist':
        return False

    app.persist('routes_map.py')
    return True


if __name__ == '__main__':
    # 提供对 python main.py persist 命令的支持
    if command_persist():
        exit(0)
    else:
        if not DEBUG_MODE:
            load_routes_map()
        # 启动内置服务器
        app.startup()
