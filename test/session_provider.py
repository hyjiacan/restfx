from typing import List, Optional

import pymysql

from autorest.base.session import IDbSessionProvider, HttpSession
from autorest.util import b64


class MysqlSessionProvider(IDbSessionProvider):
    def __init__(self, expired: int):
        self.connection = pymysql.connect(
            host='172.16.53.3',
            user='root',
            password='123asd!@#',
            database='test',
            charset='utf8',
            autocommit=True)
        super().__init__(expired)

    def execute(self, sql: str, *args):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)

        rows = None
        try:
            rows = cursor.execute(sql, args)
        except Exception as e:
            print(repr(e))
            return 0, None

        if sql.startswith('SELECT'):
            data = cursor.fetchall()
        else:
            data = None
        cursor.close()
        return rows, data

    def table_exists(self) -> bool:
        rows, _ = self.execute(
            """SELECT * FROM information_schema.tables WHERE table_name ='autorest_session' LIMIT 1""")
        return rows > 0

    def create_table(self):
        self.execute("""CREATE TABLE autorest_session (
        id VARCHAR(256) PRIMARY KEY NOT NULL,
        creation_time LONG,
        last_access_time LONG,
        store TEXT
        )""")

    def get_expired_session(self, time_before: float) -> List[str]:
        rows, data = self.execute('SELECT id FROM autorest_session WHERE last_access_time < %s', int(time_before))
        return [item['id'] for item in data]

    def get(self, session_id: str) -> Optional[HttpSession]:
        rows, data = self.execute("SELECT * FROM autorest_session WHERE id=%s LIMIT 1", session_id)
        if rows == 0:
            return None
        item = data[0]
        item['store'] = b64.dec_bytes(item['store'])
        return self.parse(item)

    def upsert(self, session_id: str, creation_time: float, last_access_time: float, store: bytes):
        data = b64.enc_str(store)
        if self.exists(session_id):
            self.execute("""UPDATE autorest_session SET last_access_time=%s, store=%s WHERE id=%s""",
                         int(last_access_time), data, session_id)
            return

        self.execute("""INSERT INTO autorest_session VALUES(%s, %s, %s, %s)""",
                     session_id,
                     int(creation_time),
                     int(last_access_time),
                     data
                     )

    def exists(self, session_id: str) -> bool:
        rows, _ = self.execute("""SELECT * FROM autorest_session WHERE id=%s""", session_id)
        return rows > 0

    def remove(self, session_id: str):
        self.execute("""DELETE FROM autorest_session WHERE id=%s""", session_id)

    def dispose(self):
        self.execute('TRUNCATE TABLE autorest_session')
        self.connection.close()
