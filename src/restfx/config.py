import os

from werkzeug.local import LocalStack

from . import __meta__
from .util import Logger


class AppConfig:
    """
    应用的配置
    """

    # 所有应用的配置集合
    _CONFIGS = {}

    def __init__(self, app_id: str,
                 app_root: str,
                 debug: bool,
                 api_prefix: str,
                 append_slash: bool,
                 strict_mode: bool,
                 api_page_enabled: bool,
                 api_page_name: str,
                 api_page_expanded: bool,
                 api_page_cache: bool,
                 api_page_addition,
                 api_page_header: str,
                 api_page_footer: str,
                 api_page_assets: tuple,
                 allowed_route_meta: dict,
                 ):
        """

        """
        self._CONFIGS[app_id] = self
        self.app_id = app_id
        self.api_prefix = api_prefix
        self.local = LocalStack()
        # 是否启用DEBUG模式
        self.debug = debug
        # 工作目录
        self.ROOT = app_root
        self.append_slash = append_slash
        self.strict_mode = strict_mode
        self.middleware_manager = None
        self.middlewares = []
        """
        注册的中间件实例集合
        :type: List[MiddlewareBase]
        """
        self.reversed_middlewares = []
        """
        :type: List[MiddlewareBase]
        """
        self.plugins = []
        """
        注册的插件实例集合
        :type: List[PluginBase]
        """

        self.routes = []
        """
        注册的路由列表
        """

        self.docs = []
        """
        注册的路由列表对应的文档信息
        """

        self.enum_types = []
        """
        系统使用到的枚举类型集合
        """

        # 路由映射表，其键为请求的路径，其值为映射的目录
        self.routes_map = {}

        self.static_map = {}

        # 注入数据/函数集合
        # 其中存放将被注入到路由函数参数列表上的数据/函数
        self.injections = {}

        # 是否启用 API 页面
        self.api_page_enabled = debug if api_page_enabled is None else api_page_enabled
        self.api_page_name = api_page_name or 'An awesome %s project' % __meta__.name
        self.api_page_expanded = api_page_expanded
        # 是否缓存API页面的 html 文件 和 接口数据
        self.api_page_cache = not debug if api_page_cache is None else api_page_cache
        self.api_page_header = api_page_header
        self.api_page_footer = api_page_footer
        self.api_page_addition = api_page_addition
        self.api_page_assets = api_page_assets
        self.allowed_route_meta = allowed_route_meta

        if self.api_page_enabled:
            self.static_map['/internal_assets'] = os.path.join(os.path.dirname(__file__), 'internal_assets')

    def dispose(self):
        if self.app_id in self._CONFIGS:
            self._CONFIGS.pop(self.app_id)

        logger = Logger._LOGGERS[self.app_id]

        for plugin in self.plugins:
            try:
                plugin.destroy()
            except Exception as e:
                logger.error('Failed to destroy plugin %r' % plugin.__name__, e)

        for middleware in self.reversed_middlewares:
            # logger.debug('Disposing middleware %r' % type(middleware).__name__)
            try:
                middleware.dispose()
            except Exception as e:
                Logger.current().error('Failed to dispose middleware %r' % middleware.__name__, e)

        del self.middlewares
        del self.reversed_middlewares
        del self.plugins
        del self.routes
        del self.enum_types
        del self.api_page_assets
        del self.routes_map
        del self.static_map

    @classmethod
    def get(cls, app_id: str):
        """

        :param app_id:
        :return:
        :rtype: AppConfig
        """
        return cls._CONFIGS.get(app_id)

    @classmethod
    def current(cls):
        from . import globs
        app_id = globs.current_app.id
        return cls.get(app_id)
