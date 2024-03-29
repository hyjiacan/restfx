# -*- coding: utf-8 -*-
import settings
from middlewares import MyMiddleware
from restfx import App
from restfx.middleware.middlewares import SessionMiddleware
from restfx.session.providers import MemorySessionProvider

# 访问 http://127.0.0.1:9127/api 查看接口页面
app = App(settings.ROOT,
          app_id=settings.APP_ID,
          api_prefix=settings.API_PREFIX,
          debug=settings.DEBUG,
          strict_mode=settings.STRICT_MODE,
          api_page_name='An awesome restfx project'
          )

app.map_routes(settings.ROUTES_MAP)
app.map_static(settings.STATIC_MAP)

app.register_middleware(
    SessionMiddleware(MemorySessionProvider(20)),
    MyMiddleware()
)

# 注册类型
# from enum import Enum
# class OpTypes(Enum):
#     Query = 1
#     Add = 2
#     Edit = 3
#     Delete = 4
# 如果你想要使用 @route(op_type=OpTypes.Query) 这样的写法，那么需要调用
# app.register_types(OpTypes)

# 路由注入
app.inject(root=settings.ROOT)


def load_routes_map():
    from dist import routes_map
    app.register_routes(routes_map.routes)


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
        import sys
        sys.exit(0)

    if not settings.DEBUG:
        load_routes_map()
    # 启动内置服务器
    app.startup(host=settings.HOST, port=settings.PORT)
