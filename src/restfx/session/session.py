import time


class HttpSession:
    def __init__(self, session_id, update_watcher, drop_watcher):
        """

        """
        self.id = session_id
        # 用于存放 session 数据项
        self.store = {}

        now = time.time()

        self.creation_time = now
        """
        创建 session 的时间
        """

        self.last_access_time = now
        """
        当前 session 对应的请求上下文最后被客户端访问的时间
        """

        self.remote_addr = ''
        """
        session 对应的客户端IP地址
        """

        self.user_agent = ''
        """
        session 对应的浏览器代理串
        """

        self._update_watcher = update_watcher
        """
        session 项变更的观察者
        """

        self._drop_watcher = drop_watcher
        """
        session 销毁的观察者
        """

        self._destroyed = False
        """
        当前是否已经被销毁
        """

        self._changed = True
        """
        session 是否有变更
        默认值指定为 True，以在新建session后，能够被存储
        """

    def __str__(self):
        return self.id

    def __getstate__(self):
        return {
            'id': self.id,
            'store': self.store,
            'creation_time': self.creation_time,
            'last_access_time': self.last_access_time,
            'remote_addr': self.remote_addr,
            'user_agent': self.user_agent,
        }

    def __setstate__(self, state):
        self.id = state['id']
        self.store = state['store']
        self.creation_time = state['creation_time']
        self.last_access_time = state['last_access_time']
        self.remote_addr = state['remote_addr']
        self.user_agent = state['user_agent']
        self._destroyed = False
        self._changed = False

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

        import sys

        # 限制存储值大小（不超过 65535)
        # 检查存储数据长度，如果大于 65535 则抛出异常
        max_value = 65535
        store_len = sys.getsizeof(self.store)
        if store_len > max_value:
            del self.store[key]
            raise RuntimeError('Entity is too large (%s) for session storage, the max value is %s: %s.' % (
                store_len, max_value, key))

        self._changed = True

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
            self._changed = True

    def flush(self):
        """
        立即将session中的变更存储，否则会在向浏览器发送响应时才会存储
        :return:
        """
        if not self._changed:
            return
        self._changed = False
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

    @classmethod
    def current(cls):
        from ..globs import session
        return session