import os
from contextlib import contextmanager
from types import FunctionType
from typing import List, Optional, Tuple

from .interfaces import IDbSessionProvider, ISessionProvider
from .session import HttpSession


class MemorySessionProvider(ISessionProvider):
    """
    基于内存的 session 管理
    注：此类型仅适用于单线程开发环境, 多线程时会出现无法预料的问题；请勿用于生产环境！
    """

    def __init__(self, expired: int = None, check_interval=30, on_expired: FunctionType = None):
        super().__init__(expired, check_interval, True, on_expired)
        self.sessions = {}

    def remove(self, session_id: str):
        if self.exists(session_id):
            del self.sessions[session_id]

    def clear(self):
        self.sessions.clear()

    def get_expired_session(self, time_before: float) -> List[str]:
        expired_sessions = []
        for session in self.sessions.values():
            if time_before > session.last_access_time:
                expired_sessions.append(session.id)
        return expired_sessions

    def get(self, session_id: str) -> Optional[HttpSession]:
        return self.sessions[session_id] if self.exists(session_id) else None

    def set(self, session: HttpSession):
        self.sessions[session.id] = session

    def exists(self, session_id: str):
        return session_id in self.sessions


class FileSessionProvider(ISessionProvider):
    def __init__(self, sessions_root: str, expired: int = None, check_interval=30, auto_clear=False,
                 on_expired: FunctionType = None):
        super().__init__(expired, check_interval, auto_clear, on_expired)

        self.sessions_root = os.path.abspath(os.path.join(sessions_root, 'restfx_sessions'))
        if not os.path.exists(self.sessions_root):
            os.makedirs(self.sessions_root)
            # print('mkdir:' + self.sessions_root)
        elif auto_clear:
            self.clear()

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

        import pickle

        with open(session_file, mode='rb') as fp:
            # noinspection PyBroadException
            try:
                session = pickle.load(fp)
                fp.close()
            except Exception:  # as e:
                # print('Failed to load session file %s: %s' % (session_file, repr(e)))
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

    def get_expired_session(self, time_before: float) -> List[str]:
        entities = os.listdir(self.sessions_root)

        sessions = []

        for entity in entities:
            last_access_time = os.path.getatime(self._get_session_path(entity))
            if time_before > last_access_time:
                sessions.append(entity)

        return sessions

    def get(self, session_id: str) -> Optional[HttpSession]:
        return self._load_session(session_id)

    def set(self, session: HttpSession):
        import pickle
        import fcntl
        # print('Set session:' + session.id)
        fp = open(self._get_session_path(session.id), mode='wb')
        fcntl.flock(fp, fcntl.LOCK_EX)
        try:
            pickle.dump(session, fp, pickle.HIGHEST_PROTOCOL)
            fp.close()
        finally:
            fcntl.flock(fp, fcntl.LOCK_UN)

    def exists(self, session_id: str):
        return os.path.isfile(self._get_session_path(session_id))

    def clear(self):
        os.removedirs(self.sessions_root)


class MySQLSessionProvider(IDbSessionProvider):
    def __init__(self, db_options: dict, table_name="restfx_sessions", expired: int = None, check_interval=30,
                 auto_clear=False, on_expired: FunctionType = None):
        """

        :param db_options: 按 `pymysql.connect` 的参数传入: host, user, password, database, port 等
        :param table_name:
        :param expired:
        :param check_interval:
        :param auto_clear:
        """
        self.table_name = table_name
        super().__init__({
            'connect_timeout': 5,
            **db_options
        }, expired, check_interval, auto_clear, on_expired)

    def execute(self, sql: str, *args, throw_except=False, ensure_table=True) -> Tuple[int, Tuple[dict]]:
        if ensure_table:
            self.ensure_table()

        import pymysql
        conn = pymysql.connect(**self.db_options)
        # print('[MySQLSessionProvider] ' + (sql % args))

        cursor = None
        rows = 0
        data = None
        try:
            import pymysql.cursors
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            rows = cursor.execute(sql, args)
            if sql.startswith('SELECT'):
                data = cursor.fetchall()
        except Exception as e:
            self.logger.error('Error occurred during executing SQL statement: %s, args=%s' % (sql, args), e)
            if throw_except:
                raise e
        else:
            conn.commit()
        finally:
            if cursor is not None:
                cursor.close()
            conn.close()

        # noinspection PyTypeChecker
        return rows, data

    def ensure_table(self):
        if self.is_db_available:
            return

        rows, _ = self.execute(
            """SELECT * FROM `information_schema`.`TABLES`
            WHERE `TABLE_SCHEMA`='{db_name}' AND `TABLE_NAME` ='{table_name}' LIMIT 1""".format(
                db_name=self.db_options['database'],
                table_name=self.table_name
            ), throw_except=True, ensure_table=False)
        if rows > 0:
            self.is_db_available = True
            if self.auto_clear:
                self.clear()
            return

        self.logger.info('Creating session table %r' % self.table_name)
        self.execute("""CREATE TABLE `{table_name}` (
        `id` VARCHAR(48) PRIMARY KEY NOT NULL,
        `creation_time` BIGINT NOT NULL,
        `last_access_time` BIGINT NOT NULL,
        `store` BLOB,
        INDEX `last_access`(`last_access_time` ASC)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8""".format(table_name=self.table_name), throw_except=True,
                     ensure_table=False)

        self.is_db_available = True

    def get_expired_session(self, time_before: float) -> List[str]:
        rows, data = self.execute(
            'SELECT `id` FROM `{table_name}` WHERE `last_access_time` < %s'.format(table_name=self.table_name),
            int(time_before))
        if rows == 0:
            return []
        return [item['id'] for item in data]

    def get(self, session_id: str) -> Optional[HttpSession]:
        rows, data = self.execute(
            "SELECT * FROM `{table_name}` WHERE `id`=%s LIMIT 1".format(table_name=self.table_name),
            session_id)
        if rows == 0:
            return None
        return self.parse(data[0])

    def upsert(self, session_id: str, creation_time: float, last_access_time: float, store: bytes):
        self.execute("""INSERT INTO `{table_name}` VALUES(%s, %s, %s, %s) ON DUPLICATE KEY UPDATE
        last_access_time=%s, store=%s""".format(table_name=self.table_name),
                     session_id,
                     int(creation_time),
                     int(last_access_time),
                     store,
                     int(last_access_time),
                     store)

    def exists(self, session_id: str) -> bool:
        rows, _ = self.execute("""SELECT 1 FROM `{table_name}` WHERE `id`=%s limit 1""".format(
            table_name=self.table_name), session_id)
        return rows > 0

    def remove(self, session_id: str):
        self.execute("""DELETE FROM `{table_name}` WHERE `id`=%s""".format(table_name=self.table_name), session_id)

    def clear(self):
        self.execute('TRUNCATE TABLE `{table_name}`'.format(table_name=self.table_name))


class RedisSessionProvider(IDbSessionProvider):
    """
    提供基于 Redis 的 session 存储支持
    """

    def __init__(self, db_options: dict, expired: int = None, check_interval=30, auto_clear=False,
                 on_expired: FunctionType = None):
        """
        :param db_options: 按 `redis.connection.Connection` 的参数传入: host, password, port=6379, db=0 等
        :param expired:
        :param check_interval:
        :param auto_clear:
        """
        super().__init__({
            'socket_timeout': 5,
            **db_options
        }, expired, check_interval, auto_clear, on_expired)
        self.started = False

    @contextmanager
    def connect(self):
        import redis

        conn = redis.Redis(**self.db_options)
        if not self.started and self.auto_clear:
            self.started = True
            conn.flushdb()
        try:
            yield conn
        finally:
            conn.close()

    def get_expired_session(self, time_before: float) -> List[str]:
        return []

    def get(self, session_id: str) -> Optional[HttpSession]:
        with self.connect() as conn:
            session = conn.get(session_id)
            if session is None:
                return session

            import pickle
            session = pickle.loads(session)
            setattr(session, '_update_watcher', self.set)
            setattr(session, '_drop_watcher', self.remove)
            return session

    def upsert(self, session_id: str, creation_time: float, last_access_time: float, store: bytes):
        raise NotImplemented()

    def set(self, session: HttpSession):
        with self.connect() as conn:
            import pickle
            buf = pickle.dumps(session, pickle.HIGHEST_PROTOCOL)
            with conn.lock('set_session'):
                result = conn.set(session.id, buf, ex=self.expired)
            return result

    def exists(self, session_id: str) -> bool:
        with self.connect() as conn:
            return conn.exists(session_id) > 0

    def remove(self, session_id: str):
        with self.connect() as conn:
            return conn.delete(session_id)

    def clear(self):
        with self.connect() as conn:
            return conn.flushdb()
