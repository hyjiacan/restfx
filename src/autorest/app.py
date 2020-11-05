import uuid
from types import MethodType

from werkzeug.serving import run_simple

from .base.app_base import AppBase
from .base.app_context import AppContext
from .util import utils


class App:
    def __init__(self,
                 app_root: str,
                 api_prefix='api',
                 with_static=False,
                 static_dir='',
                 static_path='/static',
                 debug_mode=False,
                 url_endswith_slash=False
                 ):
        self.id = uuid.uuid4()
        self.context = AppContext(self.id, app_root, debug_mode, url_endswith_slash)
        self.app = AppBase(self.context, api_prefix, with_static, static_dir, static_path)

    def startup(self, host='127.0.0.1', port=9127):
        run_simple(host, port, self.app, use_debugger=True, use_reloader=True)

    def update_debug_mode(self, debug_mode: bool):
        self.context.update_debug_mode(debug_mode)

    def collect(self, *environments):
        return self.context.collector.collect(self.context.routes_map, *environments)

    def persist(self, filename: str = '', encoding='utf8', *environments):
        return self.context.collector.persist(self.context.routes_map, filename, encoding, *environments)

    def set_intercepter(self, intercepter):
        """
        设置请求分发前的处理函数
        :param intercepter:
        :return:
        """
        self.app.router.intercepter = intercepter

    def set_logger(self, logger):
        """
        设置自定义的 logger
        :param logger:
        :return:
        """
        self.context.logger.custom_logger = logger

    def map_routes(self, routes_map: dict):
        """
        注册路由映射表
        :param routes_map:
        :return:
        """
        for path in routes_map:
            if not path:
                raise Exception('Empty route map prefix value')
            self.context.routes_map[path] = routes_map[path]

    def register_routes(self, routes: list):
        """
        手动注册路由列表
        :param routes: 其每一项都应该是一个 list, 元素依次为 method: str, path: str, handler: MethodType
        :return:
        """
        for route in routes:
            self.register(*route)

    def register(self, method: str, path: str, handler: MethodType):
        """
        手动注册路由
        :param path:
        :param method:
        :param handler:
        :return:
        """
        rid = '%s#%s' % (path, method.lower())
        if rid in self.app.router.production_routes:
            self.context.logger.warning('%s %s exists' % (method, path))

        args = utils.get_func_args(handler, self.context.logger)
        self.app.router.production_routes[rid] = {
            'func': handler,
            'args': args
        }

    def register_globals(self, *global_classes):
        """
        注册全局类型
        :type global_classes: class
        :param global_classes:
        :return:
        """
        for cls in global_classes:
            self.context.collector.global_classes.append(cls)

    def register_middleware(self, *middlewares):
        """
        注册中间件，注册的中间件将按顺序执行
        :param middlewares:
        :return:
        """
        for cls in middlewares:
            self.context.middlewares.append(cls())
