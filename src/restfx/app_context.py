from .routes.collector import Collector
from .session.interfaces import ISessionProvider
from .util.logger import Logger


class AppContext:
    contexts = {}

    def __init__(self, app_id: str,
                 app_root: str,
                 debug_mode: bool,
                 url_endswith_slash: bool,
                 session_provider: ISessionProvider,
                 sessionid_name: str):
        """

        """

        self.contexts[app_id] = self
        self.app_id = app_id
        # 是否启用DEBUG模式
        self.DEBUG = debug_mode
        # 工作目录
        self.ROOT = app_root
        self.url_endswith_slash = url_endswith_slash
        # 注册的中间件实例集合
        self.middlewares = []
        """
        :type: List[MiddlewareBase]
        """

        # 路由映射表，其键为请求的路径，其值为映射的目录
        self.routes_map = {}

        self.session_provider = session_provider
        """
        :type: ISessionProvider
        """

        self.sessionid_name = sessionid_name

        self.collector = Collector(app_root, url_endswith_slash)
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
