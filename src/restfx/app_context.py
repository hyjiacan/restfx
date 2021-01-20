import os

from restfx import __meta__

from .routes.collector import Collector
from .util.logger import Logger


class AppContext:
    contexts = {}

    def __init__(self, app_id: str,
                 app_root: str,
                 debug_mode: bool,
                 append_slash: bool):
        """

        """

        self.contexts[app_id] = self
        self.app_id = app_id
        # 是否启用DEBUG模式
        self.DEBUG = debug_mode
        # 工作目录
        self.ROOT = app_root
        self.append_slash = append_slash
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

        self.dev_options = {
            'app_name': 'An awesome %s project' % __meta__.name,
            'api_list_expanded': False
        }

        if debug_mode:
            self.static_map['/restfx_assets_for_dev'] = os.path.join(os.path.dirname(__file__), 'assets_for_dev')

        self.collector = Collector(app_root, append_slash)
        self.logger = Logger(debug_mode)
        # debug 状态变化时的处理函数
        self.debug_changed_handlers = [self.logger.on_debug_mode_changed]

    def update_debug_mode(self, debug_mode: bool):
        if debug_mode == self.DEBUG:
            return

        self.DEBUG = debug_mode

        for handler in self.debug_changed_handlers:
            # noinspection PyArgumentList
            handler(debug_mode)

    @staticmethod
    def get(app_id: str):
        """

        :param app_id:
        :return:
        :rtype: AppContext
        """
        return AppContext.contexts.get(app_id)
