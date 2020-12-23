import pickle
import time
from abc import abstractmethod, ABC
from threading import Timer
from typing import List, Optional

from .session import HttpSession


class ISessionProvider(ABC):
    """
    session 提供者基类，自定义 session 提供者时应该继承此类
    此类不可被实例化
    """

    def __init__(self, expired: int, *args, **kwargs):
        """

        :param expired: 过期时长，单位为秒
        """
        self.expired = expired
        # 每 5 秒执行一次检查
        self.timer = Timer(5, self._drop_expire_session)
        self.timer.start()

    def _drop_expire_session(self):
        time_before = time.time() - self.expired
        expired_sessions = self.get_expired_session(time_before)
        for session_id in expired_sessions:
            # print('Drop expired session:' + session.id)
            self.remove(session_id)

    def is_expired(self, session: HttpSession) -> bool:
        return time.time() - session.last_access_time > self.expired

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
        清空所有的 session，
        回收 session provider
        :return:
        """
        self.timer.join()


class IDbSessionProvider(ISessionProvider):
    def __init__(self, pool, expired: int, *args, **kwargs):
        self.pool = pool
        """
        :type: PooledDB
        """
        if not self.table_exists():
            self.create_table()
        super().__init__(expired, *args, **kwargs)

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
