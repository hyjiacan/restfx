import os
import pickle
from abc import abstractmethod, ABC
from datetime import datetime, timedelta
from threading import Timer
from types import MethodType
from typing import List


class HttpSession:
    def __init__(self, session_id):
        """

        """
        self.id = session_id
        self.store = {}
        self.create_time = datetime.now()
        self.last_access_time = datetime.now()

    def get(self, key, default=None):
        return self.store[key] if self.has(key) else default

    def set(self, key, value: [list, dict, str, int, bool, float]):
        self.store[key] = value

    def has(self, key) -> bool:
        return key in self.store

    def remove(self, key):
        if self.has(key):
            del self.store[key]

    def clear(self):
        """
        清空所有项
        :return:
        """
        self.store.clear()

    def drop(self):
        pass


class ISessionProvider(ABC):
    def __init__(self, expired: int):
        """

        :param expired: 过期时长，单位为秒
        """
        self.expired = expired
        # 每 5 秒执行一次检查
        self.timer = Timer(5, self._drop_expire_session)
        self.timer.start()

    def _drop_expire_session(self):
        expired_sessions = self.get_expired_session()
        for session in expired_sessions:
            self.remove(session)

    def is_expired(self, session: HttpSession) -> bool:
        now = datetime.now()
        seconds = (now - session.last_access_time).total_seconds()
        return seconds > self.expired

    def create(self, session_id: str) -> HttpSession:
        session = HttpSession(session_id)
        session.drop = lambda sid: self.remove(sid)
        self.set(session)
        return session

    @abstractmethod
    def get_expired_session(self) -> List[HttpSession]:
        pass

    @abstractmethod
    def get(self, session_id: str) -> HttpSession:
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
    def exists(self, session_id) -> bool:
        """
        检索指定 id 的 session 是否存在
        :param session_id:
        :return:
        """
        pass

    @abstractmethod
    def remove(self, session_id):
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
        self.timer.join()


class MemorySessionProvider(ISessionProvider):
    def __init__(self, expired: int):
        super().__init__(expired)
        self.sessions = {}

    def remove(self, session_id):
        if self.exists(session_id):
            del self.sessions[session_id]

    def get_expired_session(self) -> List[HttpSession]:
        expired_sessions = []
        now = datetime.now()
        for session in self.sessions.values():
            # 存活时长
            seconds = (now - session.last_access_time).total_seconds()
            if seconds > self.expired:
                expired_sessions.append(session)
        return expired_sessions

    def get(self, session_id: str):
        session = self.sessions[session_id]
        if self.is_expired(session):
            session.drop()
        return None

    def set(self, session: HttpSession):
        self.sessions[session.id] = session

    def exists(self, session_id):
        return session_id in self.sessions

    def dispose(self):
        self.sessions.clear()
        super().dispose()


class FileSessionProvider(ISessionProvider):
    def __init__(self, expired: int, session_path: str):
        super().__init__(expired)
        self.session_path = session_path

    def _get_session_path(self, session_id: str) -> str:
        return os.path.join(self.session_path, 'autorest_session_' + session_id)

    def remove(self, session_id):
        if not self.exists(session_id):
            return
        os.remove(self._get_session_path(session_id))

    def get_expired_session(self) -> List[HttpSession]:
        entities = os.listdir(self.session_path)

        sessions = []

        for entity in entities:
            session_file = os.path.join(self.session_path, entity)
            if os.path.isfile(session_file):
                with open(session_file, mode='r') as fp:
                    session = pickle.load(fp)
                    sessions.append(session)

        return sessions

    def get(self, session_id: str):
        if not self.exists(session_id):
            return None

        with open(self._get_session_path(session_id), mode='r') as fp:
            session = pickle.load(fp)

        if self.is_expired(session):
            session.drop()
            return None

        return session

    def set(self, session: HttpSession):
        with open(self._get_session_path(session.id), mode='w') as fp:
            pickle.dump(session, fp, pickle.HIGHEST_PROTOCOL)

    def exists(self, session_id):
        return os.path.isfile(self._get_session_path(session_id))

    def dispose(self):
        os.removedirs(self.session_path)
        super().dispose()


class DatabaseSessionProvider(ISessionProvider):
    def __init__(self, expired: int, executor: MethodType, table_name='autorest_sessions'):
        super().__init__(expired)
        self.sessions = {}
        self.executor = executor
        self.table_name = table_name

    def remove(self, session_id):
        self.executor('delete from %s where id=%s' % (self.table_name, session_id))

    def _parse(self, data) -> HttpSession:
        session = HttpSession(data['id'])
        session.create_time = datetime.fromisoformat(data['create_time'])
        session.last_access_time = datetime.fromisoformat(data['last_access_time'])
        session.store = pickle.loads(data['store'])
        session.drop = lambda sid: self.remove(sid)

        return session

    def get_expired_session(self) -> List[HttpSession]:
        expire_time = (datetime.now() + timedelta(seconds=-self.expired)).strftime('%Y-%m-%d %H:%M:%S')
        result = self.executor('select * from %s where last_access_time<%s' % (self.table_name, expire_time))

        return [
            self._parse(item)
            for item in result
        ]

    def get(self, session_id: str):
        item = self.executor('select * from %s where id=%s limit 1' % (self.table_name, session_id))
        session = self._parse(item)

        if self.is_expired(session):
            session.drop()
            return None
        return session

    def set(self, session: HttpSession):
        # .strftime('%Y-%m-%d %H:%M:%S')
        if self.exists(session.id):
            self.executor('update %s set last_access_time=%s, store=%s')
        self.sessions[session.id] = session

    def exists(self, session_id):
        return session_id in self.sessions

    def dispose(self):
        self.sessions.clear()
        super().dispose()
