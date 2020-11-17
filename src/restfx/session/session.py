import time


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
        # session 是否有变更
        self._changed = False

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
