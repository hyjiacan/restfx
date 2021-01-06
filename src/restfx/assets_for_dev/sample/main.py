# -*- coding: utf-8 -*-
import os

from restfx import App
from restfx.middleware.middlewares import SessionMiddleware
from restfx.session.providers import MemorySessionProvider
from settings import APP_ID, ROOT, DEBUG

# 可以通过 http://127.0.0.1:9127/api 查看 API 列表
app = App(APP_ID, ROOT, api_prefix='api', debug_mode=DEBUG)

app.map_routes({
    'foo': 'bar'
}).map_static({
    # 尝试访问: http://127.0.0.1:9127/static/index.html
    '/static': os.path.join(ROOT, 'static')
})

app.register_middleware(
    SessionMiddleware(MemorySessionProvider(20)),
)


def load_routes_map():
    from routes_map import routes
    app.map_routes(routes)


if DEBUG:
    app.persist('routes_map.py')
else:
    load_routes_map()

if __name__ == '__main__':
    app.startup(host='127.0.0.1', port=9127)
