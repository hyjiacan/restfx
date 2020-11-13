from typing import List, Optional

import pymysql

from autorest.base.session import IDbSessionProvider, HttpSession
from autorest.util import b64


class MysqlSessionProvider(IDbSessionProvider):
    table_name = "autorest_session"

    def __init__(self, expired: int):
        self.connection = pymysql.connect(
            host='172.16.53.3',
            user='root',
            password='123asd!@#',
            database='test',
            charset='utf8',
            autocommit=True)
        super().__init__(expired)

    def execute(self, sql: str):
        cursor = self.connection.cursor()
        rows = cursor.execute(sql.format(table_name=self.table_name))

        if sql.startswith('SELECT'):
            data = cursor.fetchall()
        else:
            data = None
        cursor.close()
        return rows, data

    def table_exists(self) -> bool:
        rows, _ = self.execute(
            """SELECT * FROM information_schema.tables WHERE table_name ='{table_name}' LIMIT 1""")
        return rows > 0

    def create_table(self):
        self.execute("""CREATE TABLE {table_name} (
        id VARCHAR(256) PRIMARY KEY NOT NULL,
        creation_time FLOAT,
        last_access_time FLOAT,
        store TEXT
        )""")

    @staticmethod
    def dataset2dict(dataset):
        return {
            'id': dataset[0],
            'creation_time': dataset[1],
            'last_access_time': dataset[2],
            'store': b64.dec_bytes(dataset[3]),
        }

    def get_expired_session(self, time_before: float) -> List[HttpSession]:
        rows, data = self.execute('SELECT * FROM {table_name} WHERE last_access_time < %d' % time_before)

        return [self.parse(self.dataset2dict(item)) for item in data]

    def get(self, session_id: str) -> Optional[HttpSession]:
        rows, data = self.execute("SELECT * FROM {table_name} WHERE id='%s' LIMIT 1" % session_id)
        if rows == 0:
            return None
        return self.parse(self.dataset2dict(data[0]))

    def upsert(self, session_id: str, creation_time: float, last_access_time: float, store: bytes):
        data = b64.enc_str(store)
        if self.exists(session_id):
            self.execute("""UPDATE {table_name} SET last_access_time=%d, store='%s' WHERE id='%s'""" % (
                last_access_time, data, session_id))
            return

        self.execute("""INSERT INTO {table_name} VALUES('%s', %d, %d, '%s')""" % (
            session_id,
            creation_time,
            last_access_time,
            data
        ))

    def exists(self, session_id: str) -> bool:
        rows, _ = self.execute("""SELECT * FROM {table_name} WHERE id='%s'""" % (session_id))
        return rows > 0

    def remove(self, session_id: str):
        self.execute("""DELETE FROM {table_name} WHERE id='%s'""" % session_id)

    def dispose(self):
        self.execute('TRUNCATE TABLE {table_name}')
        self.connection.close()
