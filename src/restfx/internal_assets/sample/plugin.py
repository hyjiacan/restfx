import os

from restfx.plugin import PluginBase

# 不要使用 settings.ROOT ，这可能导致目录错乱
ROOT = os.path.dirname(__file__)


class MyPlugin(PluginBase):
    """
    声明一个插件
    """

    def __init__(self):
        super(MyPlugin, self).__init__('MyPlugin', '0.1.0', '插件用法演示')

    def setup(self, app):
        # 注意下方的 .dist
        from .dist import routes_map
        app.register_routes(routes_map.routes)

        # 注意下方的 .middlewares
        from .middlewares import MyMiddleware
        app.register_middleware(
            MyMiddleware()
        )

        app.map_static({
            '/admin_static': os.path.join(ROOT, 'static')
        })

    def destroy(self):
        pass
