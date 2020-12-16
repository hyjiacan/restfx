import os
import uuid
from types import MethodType

from werkzeug.serving import run_simple

from .app_context import AppContext
from .session.interfaces import ISessionProvider
from .util.func_util import FunctionDescription
from .wsgi_app import WsgiApp


class App:
    def __init__(self,
                 app_root: str,
                 api_prefix='api',
                 static_map: dict = None,
                 debug_mode=False,
                 url_endswith_slash=False,
                 session_provider: ISessionProvider = None,
                 sessionid_name='SESSIONID'
                 ):
        """

        :param app_root:
        :param api_prefix:
        :param static_map:
        :param debug_mode:
        :param url_endswith_slash:
        :param session_provider:
        :param sessionid_name:
        """
        self.id = str(uuid.uuid4())
        self.context = AppContext(self.id, app_root, debug_mode, url_endswith_slash,
                                  session_provider, sessionid_name)
        self.wsgi = WsgiApp(self.context, api_prefix, static_map)

    def startup(self, host='127.0.0.1', port=9127, **kwargs):
        run_simple(host, port, self.wsgi, use_debugger=True, use_reloader=True, **kwargs)

    def update_debug_mode(self, debug_mode: bool):
        self.context.update_debug_mode(debug_mode)
        return self

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
        self.wsgi.router.intercepter = intercepter
        return self

    def set_logger(self, logger):
        """
        设置自定义的 logger
        :param logger:
        :return:
        """
        self.context.logger.custom_logger = logger
        return self

    def map_routes(self, routes_map: dict):
        """
        注册路由映射表
        :param routes_map:
        :return:
        """
        for path in routes_map:
            if not path:
                raise Exception('Empty route map prefix value')
            pkg = routes_map[path]
            pkg_path = os.path.join(self.context.ROOT, pkg.replace('.', '/'))
            if not os.path.exists(pkg_path):
                self.context.logger.warning('Route map "%s" not exists, path=%s' % (pkg, pkg_path))
            self.context.routes_map[path] = pkg
        return self

    def register_routes(self, routes: list):
        """
        手动注册路由列表
        :param routes: 其每一项都应该是一个 list, 元素依次为 method: str, path: str, handler: MethodType
        :return:
        """
        for route in routes:
            self.register(*route)
        return self

    def register(self, method: str, path: str, handler: MethodType):
        """
        手动注册路由
        :param path:
        :param method:
        :param handler:
        :return:
        """
        rid = '%s#%s' % (path, method.lower())
        if rid in self.wsgi.router.production_routes:
            self.context.logger.warning('%s %s exists' % (method, path))

        desc = FunctionDescription(handler)
        self.wsgi.router.production_routes[rid] = {
            'func': handler,
            'args': desc.arguments
        }
        return self

    def register_globals(self, *global_classes):
        """
        注册全局类型
        :type global_classes: class
        :param global_classes:
        :return:
        """
        for cls in global_classes:
            self.context.collector.global_classes.append(cls)
        return self

    def register_middleware(self, *middlewares):
        """
        注册中间件，注册的中间件将按顺序执行
        :param middlewares:
        :return:
        """
        for cls in middlewares:
            instance = cls()
            self.context.middlewares.append(instance)
            self.context.reversed_middlwares.insert(0, instance)
        return self
