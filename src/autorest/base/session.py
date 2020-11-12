import os
import pickle
from abc import abstractmethod, ABC
from datetime import datetime, timedelta
from threading import Timer
from types import MethodType
from typing import List


class HttpSession:
    def __init__(self, session_id, update_watcher, drop_watcher):
        """

        """
        self.id = session_id
        # 用于存放 session 数据项
        self.store = {}
        # 创建 session 的时间
        self.create_time = datetime.now()
        # 当前 session 对应的请求上下文最后被客户端访问的时间
        self.last_access_time = datetime.now()
        # session 项变更的观察者
        self._update_watcher = update_watcher
        # session 销毁的观察者
        self._drop_watcher = drop_watcher
        # 当前是否已经被销毁
        self._destroyed = False

    def __getstate__(self):
        return {
            'id': self.id,
            'store': self.store,
            'create_time': self.create_time,
            'last_access_time': self.last_access_time,
        }

    def __setstate__(self, state):
        self.id = state['id']
        self.store = state['store']
        self.create_time = state['create_time']
        self.last_access_time = state['last_access_time']
        self._destroyed = False

    def get(self, key, default=None):
        """
        获取 key 所指定的项，当不存在时，返回 default 指定的值
        :param key:
        :param default:
        :return:
        """
        if self._destroyed:
            return None
        return self.store[key] if self.has(key) else default

    def set(self, key, value):
        """
        设置 key 指定的项值为 value
        :param key:
        :param value:
        :return:
        """
        if self._destroyed:
            return
        self.store[key] = value
        self._update_watcher(self)

    def has(self, key) -> bool:
        """
        指定的 key 是否存在于 session 中
        :param key:
        :return:
        """
        if self._destroyed:
            return False
        return key in self.store

    def remove(self, key):
        """
        从 session 中移除指定的 key
        :param key:
        :return:
        """
        if self._destroyed:
            return
        if self.has(key):
            del self.store[key]
            self._update_watcher(self)

    def clear(self):
        """
        清空所有项
        :return:
        """
        if self._destroyed:
            return
        self.store.clear()
        self._update_watcher(self)

    def drop(self):
        """
        销毁此 session
        :return:
        """
        if self._destroyed:
            return
        self._destroyed = True
        self._drop_watcher(self.id)


class ISessionProvider(ABC):
    """
    session 提供者基类，自定义 session 提供者时应该继承此类
    此类不可被实例化
    """

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
            self.remove(session.id)

    def is_expired(self, session: HttpSession) -> bool:
        now = datetime.now()
        seconds = (now - session.last_access_time).total_seconds()
        return seconds > self.expired

    def create(self, session_id: str) -> HttpSession:
        session = HttpSession(session_id, self.set, self.remove)
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
        return self.sessions[session_id] if self.exists(session_id) else None

    def set(self, session: HttpSession):
        self.sessions[session.id] = session

    def exists(self, session_id):
        return session_id in self.sessions

    def dispose(self):
        self.sessions.clear()
        super().dispose()


class FileSessionProvider(ISessionProvider):
    def __init__(self, expired: int, path: str):
        super().__init__(expired)
        self.session_path = os.path.abspath(path)
        if not os.path.exists(self.session_path):
            os.makedirs(self.session_path)

    def _get_session_path(self, session_id: str) -> str:
        return os.path.join(self.session_path, session_id)

    def _load_session(self, session_id):
        session_file = os.path.join(self.session_path, session_id)
        if not os.path.isfile(session_file):
            return None

        if os.path.getsize(session_file) == 0:
            return None

        with open(session_file, mode='rb') as fp:
            # noinspection PyBroadException
            try:
                session = pickle.load(fp)
            except Exception:
                # 无法解析 session 文件
                # 说明session文件已经损坏，将其删除
                os.remove(session_file)
                return None
            fp.close()

            setattr(session, '_update_watcher', self.set)
            setattr(session, '_drop_watcher', self.remove)
            return session

    def remove(self, session_id):
        if not self.exists(session_id):
            return
        os.remove(self._get_session_path(session_id))

    def get_expired_session(self) -> List[HttpSession]:
        entities = os.listdir(self.session_path)

        sessions = []

        for entity in entities:
            session = self._load_session(entity)
            if session is not None:
                sessions.append(session)

        return sessions

    def get(self, session_id: str):
        return self._load_session(session_id)

    def set(self, session: HttpSession):
        with open(self._get_session_path(session.id), mode='wb') as fp:
            pickle.dump(session, fp, pickle.HIGHEST_PROTOCOL)
            fp.close()

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
        session = HttpSession(data['id'], self.set, self.remove)
        session.create_time = datetime.fromisoformat(data['create_time'])
        session.last_access_time = datetime.fromisoformat(data['last_access_time'])
        session.store = pickle.loads(data['store'])

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
