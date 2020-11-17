import os
import pickle
from typing import List, Optional

import pymysql

from .interfaces import ISessionProvider, IDbSessionProvider
from .session import HttpSession
from ..util import b64


class MemorySessionProvider(ISessionProvider):
    def __init__(self, expired: int):
        self.sessions = {}
        super().__init__(expired)

    def remove(self, session_id: str):
        if self.exists(session_id):
            del self.sessions[session_id]

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

    def dispose(self):
        self.sessions.clear()
        super().dispose()


class FileSessionProvider(ISessionProvider):
    def __init__(self, expired: int, sessions_root: str):
        self.sessions_root = os.path.abspath(os.path.join(sessions_root, 'restfx_sessions'))
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
            except Exception:  # as e:
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
        # print('Set session:' + session.id)
        with open(self._get_session_path(session.id), mode='wb') as fp:
            pickle.dump(session, fp, pickle.HIGHEST_PROTOCOL)
            fp.close()

    def exists(self, session_id: str):
        return os.path.isfile(self._get_session_path(session_id))

    def dispose(self):
        os.removedirs(self.sessions_root)
        super().dispose()


class MysqlSessionProvider(IDbSessionProvider):
    def __init__(self, pool, table_name="restfx_sessions", expired=20):
        self.table_name = table_name

        super().__init__(pool, expired)

    def execute(self, sql: str, *args):
        conn = self.connect()

        cursor = None
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            rows = cursor.execute(sql, args)

            if sql.startswith('SELECT'):
                data = cursor.fetchall()
            else:
                data = None
        except Exception as e:
            print(repr(e))
            return 0, None
        finally:
            if cursor is not None:
                cursor.close()
            conn.close()

        return rows, data

    def table_exists(self) -> bool:
        rows, _ = self.execute(
            """SELECT 1 FROM information_schema.tables
            WHERE table_name ='{table_name}' LIMIT 1""".format(table_name=self.table_name))
        return rows > 0

    def create_table(self):
        self.execute("""CREATE TABLE {table_name} (
        id VARCHAR(256) PRIMARY KEY NOT NULL,
        creation_time LONG NOT NULL,
        last_access_time LONG NOT NULL,
        store TEXT,
        INDEX last_access(last_access_time(8) ASC)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8""".format(table_name=self.table_name))

    def get_expired_session(self, time_before: float) -> List[str]:
        rows, data = self.execute(
            'SELECT id FROM {table_name} WHERE last_access_time < %s'.format(table_name=self.table_name),
            int(time_before))
        return [item['id'] for item in data]

    def get(self, session_id: str) -> Optional[HttpSession]:
        rows, data = self.execute("SELECT * FROM {table_name} WHERE id=%s LIMIT 1".format(table_name=self.table_name),
                                  session_id)
        if rows == 0:
            return None
        item = data[0]
        item['store'] = b64.dec_bytes(item['store'])
        return self.parse(item)

    def upsert(self, session_id: str, creation_time: float, last_access_time: float, store: bytes):
        data = b64.enc_str(store)

        self.execute("""INSERT INTO {table_name} VALUES(%s, %s, %s, %s) ON DUPLICATE KEY UPDATE
        last_access_time=%s, store=%s""".format(table_name=self.table_name),
                     session_id,
                     int(creation_time),
                     int(last_access_time),
                     data,
                     int(last_access_time),
                     data)

    def exists(self, session_id: str) -> bool:
        rows, _ = self.execute("""SELECT 1 FROM {table_name} WHERE id=%s limit 1""".format(table_name=self.table_name),
                               session_id)
        return rows > 0

    def remove(self, session_id: str):
        self.execute("""DELETE FROM {table_name} WHERE id=%s""".format(table_name=self.table_name), session_id)

    def dispose(self):
        self.execute('TRUNCATE TABLE {table_name}'.format(table_name=self.table_name))
