import json
import os

from restfx.session.providers import MemorySessionProvider
from test.tools.enums import OpTypes

from midlewares import MiddlewareA
from restfx import App
from restfx.http import HttpRequest, HttpResponse
from restfx.http.response import HttpRedirect
from restfx.middleware.middlewares import HttpAuthMiddleware, SessionMiddleware
from restfx.middleware.middlewares.timetick import TimetickMiddleware
from restfx.routes import RouteMeta

root = os.path.dirname(__file__)


# db_pool = PooledDB(
#     # 使用链接数据库的模块
#     creator=pymysql,
#     # 连接池允许的最大连接数，0和None表示不限制连接数
#     maxconnections=6,
#     # 初始化时，链接池中至少创建的空闲的链接，0表示不创建
#     mincached=2,
#     # 链接池中最多闲置的链接，0和None不限制
#     maxcached=5,
#     # 链接池中最多共享的链接数量，0和None表示全部共享。
#     # PS: 无用，因为pymysql和MySQLdb等模块的 threadsafety都为1，所有值无论设置为多少，_maxcached永远为0，所以永远是所有链接都共享。
#     maxshared=1,
#     # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，不等待然后报错
#     blocking=True,
#     # 一个链接最多被重复使用的次数，None表示无限制
#     maxusage=None,
#     # 开始会话前执行的命令列表。如：["set datestyle to ...", "set time zone ..."]
#     setsession=[],
#     # ping MySQL服务端，检查是否服务可用。
#     # 如：0 = None = never,
#     # 1 = default = whenever it is requested,
#     # 2 = when a cursor is created,
#     # 4 = when a query is executed,
#     # 7 = always
#     ping=0,
#     host='172.16.53.3',
#     port=3306,
#     user='root',
#     password='123asd!@#',
#     database='test',
#     charset='utf8',
#     autocommit=True
# )
# session_provider = MysqlSessionProvider(db_pool)

def test_id(request: HttpRequest, **kwargs):
    return HttpResponse(json.dumps(kwargs))


DEBUG_MODE = True

app_id = '82615610-3aa5-491e-aa58-fab3a9561e64'


def api_page_addition(route):
    if 'auth' not in route['kwargs'] or route['kwargs'] is False:
        return '<span style="color: #ff7d7d">[需要身份校验]</span>'
    return '<span style="color: #66c0de">[不需要身份校验]</span>'


app = App(root,
          app_id=app_id,
          debug=DEBUG_MODE,
          strict_mode=True,
          api_page_enabled=True,
          api_page_name='restfx 测试项目',
          api_page_addition=api_page_addition,
          api_page_expanded=True,
          api_page_cache=None)

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


app.register_middleware(
    TimetickMiddleware(),
    HttpAuthMiddleware(on_auth),
    SessionMiddleware(MemorySessionProvider(20)),
    MiddlewareA(),
    # MiddlewareB(),
    # MiddlewareC()
)
app.inject(injection='try1try')


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
