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
          strict_mode=settings.STRICT_MODE
          )

app.map_routes(settings.ROUTES_MAP)
app.map_static(settings.STATIC_MAP)

app.register_middleware(
    SessionMiddleware(MemorySessionProvider(20)),
)

# 路由注入
app.inject(root=settings.ROOT)


# 可以通过此方法动态修改调试模式
# app.update_debug_mode(True)

def load_routes_map():
    from routes_map import routes
    app.map_routes(routes)


if settings.DEBUG:
    # app.persist('routes_map.py')
    pass
else:
    load_routes_map()

if __name__ == '__main__':
    app.startup(host=settings.HOST, port=settings.PORT)
