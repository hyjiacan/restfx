import os
import pickle
import time
from abc import abstractmethod, ABC
from threading import Timer
from typing import List, Optional


class HttpSession:
    def __init__(self, session_id, update_watcher, drop_watcher):
        """

        """
        self.id = session_id
        # 用于存放 session 数据项
        self.store = {}

        now = time.time()

        # 创建 session 的时间
        self.creation_time = now
        # 当前 session 对应的请求上下文最后被客户端访问的时间
        self.last_access_time = now
        # session 项变更的观察者
        self._update_watcher = update_watcher
        # session 销毁的观察者
        self._drop_watcher = drop_watcher
        # 当前是否已经被销毁
        self._destroyed = False

    def __str__(self):
        return self.id

    def __getstate__(self):
        return {
            'id': self.id,
            'store': self.store,
            'creation_time': self.creation_time,
            'last_access_time': self.last_access_time,
        }

    def __setstate__(self, state):
        self.id = state['id']
        self.store = state['store']
        self.creation_time = state['creation_time']
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

    def flush(self):
        """
        立即将session中的变更存储，否则会在向浏览器发送响应时才会存储
        :return:
        """
        self._update_watcher(self)

    def clear(self):
        """
        清空所有项并销毁此 session
        :return:
        """
        if self._destroyed:
            return
        self._destroyed = True
        self.store.clear()
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
        time_before = time.time() - self.expired
        expired_sessions = self.get_expired_session(time_before)
        for session in expired_sessions:
            # print('Drop expired session:' + session.id)
            self.remove(session.id)

    def is_expired(self, session: HttpSession) -> bool:
        return time.time() - session.last_access_time > self.expired

    def create(self, session_id: str) -> HttpSession:
        session = HttpSession(session_id, self.set, self.remove)
        # 实际存储了数据再创建
        # self.set(session)
        return session

    @abstractmethod
    def get_expired_session(self, time_before: float) -> List[HttpSession]:
        """
        查询已经过期的 session
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


class MemorySessionProvider(ISessionProvider):
    def __init__(self, expired: int):
        self.sessions = {}
        super().__init__(expired)

    def remove(self, session_id: str):
        if self.exists(session_id):
            del self.sessions[session_id]

    def get_expired_session(self, time_before: float) -> List[HttpSession]:
        expired_sessions = []
        for session in self.sessions.values():
            if time_before > session.last_access_time:
                expired_sessions.append(session)
        return expired_sessions

    def get(self, session_id: str) -> Optional[HttpSession]:
        return self.sessions[session_id] if self.exists(session_id) else None

    def set(self, session: HttpSession):
        self.sessions[session.id] = session

    def exists(self, session_id: str):
        return session_id in self.sessions

    def dispose(self):
        self.sessions.clear()
        super().dispose()


class FileSessionProvider(ISessionProvider):
    def __init__(self, expired: int, sessions_root: str):
        self.sessions_root = os.path.abspath(sessions_root)
        if not os.path.exists(self.sessions_root):
            os.makedirs(self.sessions_root)
            # print('mkdir:' + self.sessions_root)
        super().__init__(expired)

    def _get_session_path(self, session_id: str) -> str:
        # session_id 中可能存在 / 符号
        return os.path.join(self.sessions_root, session_id.replace('/', '_'))

    def _load_session(self, session_id: str):
        # print('Load session: ' + session_id)
        session_file = self._get_session_path(session_id)
        if not os.path.isfile(session_file):
            # print('The session currently loading not exists:' + session_file)
            return None

        if os.path.getsize(session_file) == 0:
            # print('The session currently loading is empty:' + session_file)
            return None

        with open(session_file, mode='rb') as fp:
            # noinspection PyBroadException
            try:
                session = pickle.load(fp)
                fp.close()
            except Exception as e:
                # print('Load session file %s failed: %s' % (session_file, repr(e)))
                fp.close()
                # 无法解析 session 文件
                # 说明session文件已经损坏，将其删除
                os.remove(session_file)
                return None

            setattr(session, '_update_watcher', self.set)
            setattr(session, '_drop_watcher', self.remove)
            return session

    def remove(self, session_id: str):
        # print('Remove session:' + session_id)
        session_file = self._get_session_path(session_id)
        if not self.exists(session_file):
            # print("The session to remove is not exists:" + session_file)
            return
        os.remove(session_file)

    def get_expired_session(self, time_before: float) -> List[HttpSession]:
        entities = os.listdir(self.sessions_root)

        sessions = []

        for entity in entities:
            last_access_time = os.path.getatime(self._get_session_path(entity))
            if time_before > last_access_time:
                session = self._load_session(entity)
                if session is None:
                    continue

                sessions.append(session)

        return sessions

    def get(self, session_id: str) -> Optional[HttpSession]:
        return self._load_session(session_id)

    def set(self, session: HttpSession):
        # print('Set session:' + session.id)
        with open(self._get_session_path(session.id), mode='wb') as fp:
            pickle.dump(session, fp, pickle.HIGHEST_PROTOCOL)
            fp.close()

    def exists(self, session_id: str):
        return os.path.isfile(self._get_session_path(session_id))

    def dispose(self):
        os.removedirs(self.sessions_root)
        super().dispose()


class IDbSessionProvider(ISessionProvider):
    def __init__(self, expired: int):
        if not self.table_exists():
            self.create_table()
        super().__init__(expired)

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
        session.creation_time = data['creation_time']
        session.last_access_time = data['last_access_time']
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
