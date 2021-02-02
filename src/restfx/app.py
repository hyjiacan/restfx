import os
from types import FunctionType

from werkzeug.exceptions import NotFound
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.routing import Map, Rule
from werkzeug.serving import run_simple

from .context import AppContext
from .http import HttpServerError, HttpNotFound, HttpRequest
from .routes.router import Router
from .util.func_util import FunctionDescription


class App:
    def __init__(self,
                 app_id: str,
                 app_root: str,
                 api_prefix='api',
                 debug_mode=False,
                 append_slash=False,
                 strict_mode=False,
                 enable_api_page=None
                 ):
        """

        :param app_id: 全局的唯一 id, 用于标识一个APP。可以通过 AppContext.get(id) 获取应用的 Context
        :param app_root:
        :param api_prefix:
        :param debug_mode:
        :param append_slash:
        :param strict_mode:
        :param enable_api_page:
        """

        self.id = app_id
        self.context = AppContext(self.id, app_root, debug_mode, append_slash, strict_mode, enable_api_page)

        self.api_prefix = api_prefix
        self.router = Router(self.context)

        self.custom_url_map = {}

        self.url_map = Map([
            Rule('/%s%s' % (api_prefix, '/' if append_slash else ''), endpoint='api_list'),
            Rule('/%s/<path:entry>%s' % (api_prefix, '/' if append_slash else ''), endpoint='entry_only')
        ])

    def handle_wsgi_request(self, environ, start_response):
        """
        接收并处理来自 wsgi 的请求
        :param environ:
        :param start_response:
        :return:
        """
        request = None
        try:
            request = HttpRequest(environ, self.context.app_id)
            adapter = self.url_map.bind_to_environ(environ)

            endpoint, values = adapter.match()
            if endpoint == 'api_list':
                response = self.router.api_list(request)
            elif endpoint == 'entry_only':
                response = self.router.dispatch(request, values['entry'])
            elif endpoint in self.custom_url_map:
                response = self.custom_url_map[endpoint](request, **values)
            else:
                response = HttpNotFound()
        except Exception as e:
            if isinstance(e, NotFound):
                response = HttpNotFound()
            elif self.context.DEBUG:
                raise e
            else:
                response = HttpServerError()

            msg = repr(e)
            if request:
                msg += ':' + request.path
            self.context.logger.warning(msg)

        return response(environ, start_response)

    def __call__(self, environ, start_response):
        """
        wsgi 入口
        :param environ:
        :param start_response:
        :return:
        """
        if not self.context.static_map:
            return self.handle_wsgi_request(environ, start_response)

        return SharedDataMiddleware(self.handle_wsgi_request, self.context.static_map)(
            environ, start_response)

    def update_debug_mode(self, debug_mode: bool):
        """
        更新调试模式
        :param debug_mode:
        :return:
        """
        self.context.update_debug_mode(debug_mode)
        return self

    def startup(self, host='127.0.0.1', port=9127, threaded=True, **kwargs):
        """
        开发时使用的服务器，一般来说，应仅用于开发
        :param host:
        :param port:
        :param threaded:
        :param kwargs: 适用于 werkzueg 的 run_simple 函数的其它参数
        :return:
        """
        from restfx.util import helper
        debug_mode = self.context.DEBUG

        if debug_mode:
            helper.print_meta('dev-server *DEBUG MODE*')
        else:
            helper.print_meta('dev-server')

        if self.context.enable_api_page:
            print(' * Table of APIs: http://%s:%s/%s%s' % (
                host, port, self.api_prefix, '/' if self.context.append_slash else ''
            ))

        run_simple(host, port, self, use_debugger=debug_mode, use_reloader=debug_mode, threaded=threaded, **kwargs)

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
        self.router.intercepter = intercepter
        return self

    def set_logger(self, logger):
        """
        设置自定义的 logger
        :param logger:
        :return:
        """
        self.context.logger.custom_logger = logger
        return self

    def map_urls(self, urls_map: dict):
        """
        自定义的 url 映射，这些映射不会经过路由处理，而是直接来自 werkzeug
        :param urls_map:
        :return:
        """
        for url in urls_map:
            self.custom_url_map[url] = urls_map[url]
            self.url_map.add(Rule(url, endpoint=url))
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
        if rid in self.router.production_routes:
            self.context.logger.warning('%s %s exists' % (method, path))

        desc = FunctionDescription(handler)
        self.router.production_routes[rid] = {
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

    def set_dev_options(self, **kwargs):
        """
        """
        self.context.dev_options.update(**kwargs)
        return self

    def inject(self, **kwargs):
        self.context.injections.update(**kwargs)
        return self

    @staticmethod
    def get(app_id: str):
        """

        :param app_id:
        :return:
        :rtype: AppContext
        """
        return App.contexts.get(app_id)
