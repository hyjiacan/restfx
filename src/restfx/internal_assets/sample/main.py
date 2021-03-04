# -*- coding: utf-8 -*-
import settings
from restfx import App
from restfx.middleware.middlewares import SessionMiddleware
from restfx.session.providers import MemorySessionProvider

# 访问 http://127.0.0.1:9127/api 查看接口页面
app = App(settings.APP_ID,
          settings.ROOT,
          api_prefix=settings.API_PREFIX,
          debug_mode=settings.DEBUG,
          strict_mode=settings.STRICT_MODE,
          api_page_name='An awesome restfx project'
          )

app.map_routes(settings.ROUTES_MAP)
app.map_static(settings.STATIC_MAP)

app.register_middleware(
    SessionMiddleware(MemorySessionProvider(20)),
)

# 路由注入
app.inject(root=settings.ROOT)


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
        if not settings.DEBUG:
            load_routes_map()
        # 启动内置服务器
        app.startup(host=settings.HOST, port=settings.PORT)
