# -*- coding: utf-8 -*-
import os

import settings
from restfx import App
from restfx.middleware.middlewares import SessionMiddleware
from restfx.session.providers import MemorySessionProvider

# 访问 http://127.0.0.1:9127/api 查看接口页面
app = App(settings.APP_ID,
          settings.ROOT,
          api_prefix='api',
          debug_mode=settings.DEBUG,
          append_slash=False,
          strict_mode=False,
          enable_api_page=None
          )

app.map_routes({
    'foo': 'bar'
}).map_static({
    # 尝试访问: http://127.0.0.1:9127/static/index.html
    '/static': os.path.join(settings.ROOT, 'static')
})

app.register_middleware(
    SessionMiddleware(MemorySessionProvider(20)),
)

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
    app.startup(host='127.0.0.1', port=9127)
