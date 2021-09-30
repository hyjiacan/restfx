import time
from abc import ABC, abstractmethod
from threading import Timer
from typing import List, Optional

from .session import HttpSession


class ISessionProvider(ABC):
    """
    session 提供者基类，自定义 session 提供者时应该继承此类
    此类不可被实例化
    """

    def __init__(self, expired: int, check_interval: int, auto_clear: bool):
        """

        :param expired: 过期时长，单位为秒，默认为 10分钟。指定为 0表示不会自动过期
        :param check_interval: 检查 session 是否过期的周期，单位为秒，指定为 0 时不检查
        :param auto_clear: 是否在停止/启动时，自动清空 session 存储
        """
        from restfx.util import Logger
        from restfx import globs
        self._logger = Logger.get(globs.current_app.id)
        self.auto_clear = auto_clear

        self.expired = 10 * 60 if expired is None else expired

        # 不会过期，不用启动定时器
        if self.expired > 0 and check_interval > 0:
            # 每 5 秒执行一次检查
            self.timer = Timer(check_interval, self.drop_expired_session)
            self.timer.start()

    def drop_expired_session(self):
        time_before = time.time() - self.expired
        expired_sessions = self.get_expired_session(time_before)
        for session_id in expired_sessions:
            # self._logger.debug('Drop expired session: ' + session_id)
            self.remove(session_id)

    def is_expired(self, session: HttpSession) -> bool:
        if self.expired > 0:
            return time.time() - session.last_access_time > self.expired
        return False

    def create(self, session_id: str) -> HttpSession:
        session = HttpSession(session_id, self.set, self.remove)
        # 实际存储了数据再创建
        # self.set(session)
        return session

    @abstractmethod
    def get_expired_session(self, time_before: float) -> List[str]:
        """
        查询已经过期的 session 的 id
        :param time_before: 在此时间之前的 session 即为过期
        :return:
        """
        pass

    @abstractmethod
    def get(self, session_id: str) -> Optional[HttpSession]:
        """
        获取指定 id 的 session
        :param session_id:
        :return:
        """
        pass

    @abstractmethod
    def set(self, session: HttpSession):
        """
        添加或更新指定的 session
        :param session:
        :return:
        """
        pass

    @abstractmethod
    def exists(self, session_id: str) -> bool:
        """
        检索指定 id 的 session 是否存在
        :param session_id:
        :return:
        """
        pass

    @abstractmethod
    def remove(self, session_id: str):
        """
        销毁一个 session
        :param session_id:
        :return:
        """

    @abstractmethod
    def clear(self):
        """
        清空所有 session
        :return:
        """
        pass

    def dispose(self):
        """
        回收 session provider
        :return:
        """
        self.timer.cancel()
        self.timer.join()
        if self.auto_clear:
            self.clear()


class IDbSessionProvider(ISessionProvider):
    def __init__(self, pool_options: dict, expired: int, check_interval: int, auto_clear=False):
        super().__init__(expired, check_interval, auto_clear)

        from dbutils.pooled_db import PooledDB
        self.pool_option = pool_options
        self.pool = PooledDB(**pool_options)
        self.is_db_available = False

    def connect(self, shareable=True):
        return self.pool.connection(shareable)

    def drop_expired_session(self):
        if self.is_db_available:
            super(IDbSessionProvider, self).drop_expired_session()

    def parse(self, data: dict) -> HttpSession:
        """
        用于将字典转换成 HttpSession 对象
        :param data:
        :return:
        """
        import pickle
        session = HttpSession(data['id'], self.set, self.remove)
        session.creation_time = int(data['creation_time'])
        session.last_access_time = int(data['last_access_time'])
        session.store = pickle.loads(data['store'])

        return session

    def set(self, session: HttpSession):
        import pickle
        self.upsert(session.id,
                    session.creation_time,
                    session.last_access_time,
                    pickle.dumps(session.store))

    @abstractmethod
    def upsert(self, session_id: str, creation_time: float, last_access_time: float, store: bytes):
        pass

    def dispose(self):
        self.pool.close()
        super(IDbSessionProvider, self).dispose()
