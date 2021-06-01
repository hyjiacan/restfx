import pickle
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

    def __init__(self, expired: int):
        """

        :param expired: 过期时长，单位为秒，默认为 10分钟。指定为 0表示不会自动过期
        """
        self.expired = 10 * 60 if expired is None else expired

        # 不会过期，不用启动定时器
        if self.expired > 0:
            # 每 5 秒执行一次检查
            self.timer = Timer(5, self._drop_expire_session)
            self.timer.start()

    def _drop_expire_session(self):
        time_before = time.time() - self.expired
        expired_sessions = self.get_expired_session(time_before)
        for session_id in expired_sessions:
            # print('Drop expired session:' + session_id)
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
    def dispose(self):
        """
        回收 session provider
        :return:
        """
        self.timer.cancel()
        self.timer.join()


class IDbSessionProvider(ISessionProvider):
    def __init__(self, pool_options: dict, expired: int):
        from dbutils.pooled_db import PooledDB
        self.pool_option = pool_options
        self.pool = PooledDB(**pool_options)
        # fixme 如果启动时数据库无法连接，也应该允许程序启动，而不是抛出异常
        # 更好的做法是在第一次执行 execute 时作此检查
        if not self.table_exists():
            self.create_table()
        super().__init__(expired)

    def connect(self, shareable=True):
        return self.pool.connection(shareable)

    @abstractmethod
    def table_exists(self) -> bool:
        """
        判断 session 表是否存在
        :return:
        """
        pass

    @abstractmethod
    def create_table(self):
        """
        创建 session 表
        :return:
        """
        pass

    def parse(self, data: dict) -> HttpSession:
        """
        用于将字典转换成 HttpSession 对象
        :param data:
        :return:
        """
        session = HttpSession(data['id'], self.set, self.remove)
        session.creation_time = int(data['creation_time'])
        session.last_access_time = int(data['last_access_time'])
        session.store = pickle.loads(data['store'])

        return session

    def set(self, session: HttpSession):
        self.upsert(session.id,
                    session.creation_time,
                    session.last_access_time,
                    pickle.dumps(session.store))

    @abstractmethod
    def upsert(self, session_id: str, creation_time: float, last_access_time: float, store: bytes):
        pass

    @abstractmethod
    def dispose(self):
        self.pool.close()
        super(IDbSessionProvider, self).dispose()
