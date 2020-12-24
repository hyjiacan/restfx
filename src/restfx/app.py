import os
import uuid
from types import FunctionType

from werkzeug.serving import run_simple

from . import __meta__
from .app_context import AppContext
from .util.func_util import FunctionDescription
from .wsgi_app import WsgiApp


class App:
    def __init__(self,
                 app_root: str,
                 api_prefix='api',
                 debug_mode=False,
                 url_endswith_slash=False
                 ):
        """

        :param app_root:
        :param api_prefix:
        :param debug_mode:
        :param url_endswith_slash:
        """
        # 全局的唯一 id, 用于标识一个APP
        # 可以用于在 AppContext.get(id) 处获取应用的 Context
        self.id = str(uuid.uuid4())
        self.context = AppContext(self.id, app_root, debug_mode, url_endswith_slash)
        # 暴露的 wsgi 接口，在部署时通过此接口与 wsgi 服务器通信
        self.wsgi = WsgiApp(self.context, api_prefix, url_endswith_slash)

    def update_debug_mode(self, debug_mode: bool):
        """
        更新调试模式
        :param debug_mode:
        :return:
        """
        self.context.update_debug_mode(debug_mode)
        return self

    def startup(self, host='127.0.0.1', port=9127, **kwargs):
        """
        开发时使用的服务器，一般来说，应仅用于开发
        :param host:
        :param port:
        :param kwargs: 适用于 werkzueg 的 run_simple 函数的其它参数
        :return:
        """
        print("Powered by %s %s" % (__meta__.name, __meta__.version))
        debug_mode = self.context.DEBUG
        run_simple(host, port, self.wsgi,
                   use_debugger=debug_mode, use_reloader=debug_mode, **kwargs)

    def collect(self, *global_classes):
        """
        收集路由
        :param global_classes: 指定路由装饰器上用到的全局类型
        :return:
        """
        return self.context.collector.collect(self.context.routes_map, *global_classes)

    def persist(self, filename: str = '', encoding='utf8', *global_classes):
        """
        持久化路由信息到文件
        :param filename: 不指定此值时，此函数会返回路由文件内容
        :param encoding:
        :param global_classes:
        :return:
        """
        return self.context.collector.persist(self.context.routes_map, filename, encoding, *global_classes)

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

    def map_static(self, static_map: dict):
        """
        设置静态资源目录映射
        :param static_map:
        :return:
        """
        for prefix in static_map:
            # 静态资源的前缀，必须以 / 开头
            if prefix[0] != '/':
                self.context.logger.warning(
                    'Invalid prefix of static map, it should start with "/": %s' % prefix)
                continue
            if prefix.lower() == '/restfx_assets_for_dev':
                self.context.logger.warning(
                    'The prefix of static map is reserved, pick another one please: %s' % prefix)
                continue
            target_path = static_map[prefix]
            abs_target_path = os.path.abspath(os.path.join(self.context.ROOT, target_path))
            # 无论目录是否存在都注册，因为静态目录可能是动态生成的
            self.context.static_map[prefix] = abs_target_path
            if os.path.exists(abs_target_path):
                self.context.logger.debug('Map static url %s to path %s' % (prefix, abs_target_path))
            else:
                self.context.logger.warning(
                    'The target path of static url %s not found: %s' % (prefix, abs_target_path))
        return self

    def register_routes(self, routes: list):
        """
        手动注册路由列表
        :param routes: 其每一项都应该是一个 list, 元素依次为 method: str, path: str, handler: FunctionType
        :return:
        """
        for route in routes:
            self.register(*route)
        return self

    def register(self, method: str, path: str, handler: FunctionType):
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
        :param middlewares: 中间件实例列表
        :return:
        """
        for middleware in middlewares:
            self.context.middlewares.append(middleware)
            self.context.reversed_middlwares.insert(0, middleware)
        return self
