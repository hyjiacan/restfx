import os

from restfx import __meta__
from .routes.collector import Collector
from .util.logger import Logger

# 所有应用的上下文集合
_CONTEXTS = {}


class AppContext:
    """
    应用的上下文环境
    """

    def __init__(self, app_id: str,
                 app_root: str,
                 debug: bool,
                 append_slash: bool,
                 strict_mode: bool,
                 api_page_enabled: bool,
                 api_page_name: str,
                 api_page_expanded: bool,
                 api_page_cache: bool,
                 api_page_addition):
        """

        """
        _CONTEXTS[app_id] = self
        self.app_id = app_id
        # 是否启用DEBUG模式
        self.debug = debug
        # 是否启用 API 页面
        self.api_page_enabled = debug if api_page_enabled is None else api_page_enabled
        # 工作目录
        self.ROOT = app_root
        self.append_slash = append_slash
        self.strict_mode = strict_mode
        # 注册的中间件实例集合
        self.middlewares = []
        """
        :type: List[MiddlewareBase]
        """
        self.reversed_middlwares = []
        """
        :type: List[MiddlewareBase]
        """

        # 路由映射表，其键为请求的路径，其值为映射的目录
        self.routes_map = {}

        self.static_map = {}

        # 注入数据/函数集合
        # 其中存放将被注入到路由函数参数列表上的数据/函数
        self.injections = {}

        self.api_page_options = {
            'api_page_name': api_page_name or 'Another awesome %s project' % __meta__.name,
            'api_page_expanded': api_page_expanded,
            # 是否缓存API页面的 html 文件 和 接口数据
            'api_page_cache': api_page_cache,
            'api_page_addition': api_page_addition
        }

        if self.api_page_enabled:
            self.static_map['/internal_assets'] = os.path.join(os.path.dirname(__file__), 'internal_assets')

        self.collector = Collector(app_root, append_slash)
        self.logger = Logger(debug)

    def __del__(self):
        if self.app_id in _CONTEXTS:
            del _CONTEXTS[self.app_id]
        del self.middlewares

    @staticmethod
    def get(app_id: str):
        """

        :param app_id:
        :return:
        :rtype: AppContext
        """
        return _CONTEXTS.get(app_id)
