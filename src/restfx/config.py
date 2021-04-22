import os

from werkzeug.local import LocalStack

from restfx import __meta__


class AppConfig:
    """
    应用的配置
    """

    # 所有应用的配置集合
    _CONFIGS = {}

    def __init__(self, app_id: str,
                 app_root: str,
                 debug: bool,
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
                 ):
        """

        """
        self._CONFIGS[app_id] = self
        self.app_id = app_id
        self.local = LocalStack()
        # 是否启用DEBUG模式
        self.debug = debug
        # 工作目录
        self.ROOT = app_root
        self.append_slash = append_slash
        self.strict_mode = strict_mode
        self.middleware_manager = None
        # 注册的中间件实例集合
        self.middlewares = []
        """
        :type: List[MiddlewareBase]
        """
        self.reversed_middlewares = []
        """
        :type: List[MiddlewareBase]
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

        if self.api_page_enabled:
            self.static_map['/internal_assets'] = os.path.join(os.path.dirname(__file__), 'internal_assets')

    def __del__(self):
        if self.app_id in self._CONFIGS:
            del self._CONFIGS[self.app_id]
        del self.middlewares
        del self.reversed_middlewares

    @classmethod
    def get(cls, app_id: str):
        """

        :param app_id:
        :return:
        :rtype: AppConfig
        """
        return cls._CONFIGS.get(app_id)
