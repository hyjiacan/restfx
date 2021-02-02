import string
import time

from ...context import AppContext
from ...middleware.interface import MiddlewareBase
from ...session.interfaces import ISessionProvider
from ...util import md5, b64

"""
session id 算法:

其中包含 useragent 和 remote_addr 用于标识一个远程客户端
    其值组合成 remote_addr#useragent，计算得到 md5 (length=32)
在得到的 md5 后添加随机字符(length=32)，得到一个 64 位长的串

使用 app id 分别对 md5 和随机串进行 xor 计算，得到的即是 密文 (session id)
"""

_salt = 'hyjiacan'
_salt_chars = [ord(ch) for ch in list(_salt)]
_padding_len = 24
_padding_chars = string.ascii_letters + string.digits


def _get_padding_chars():
    import random
    return _salt_chars + [ord(ch) for ch in random.sample(_padding_chars, _padding_len)]


def _encrypt_session_id(key, app_id):
    a = [ord(ch) for ch in key]
    b = _get_padding_chars()

    for i in range(32):
        a[i] = a[i] ^ app_id[i]
        b[i] = b[i] ^ app_id[i]

    return b64.enc_str(bytes(a + b))


def _decrypt_session_id(session_id, app_id):
    temp = list(b64.dec_bytes(session_id))
    a = temp[0:32]
    b = temp[32:]

    key = []
    padding = []

    for i in range(32):
        key.append(chr(a[i] ^ app_id[i]))
        padding.append(chr(b[i] ^ app_id[i]))

    if not ''.join(padding).startswith(_salt):
        return None

    return ''.join(key)


class SessionMiddleware(MiddlewareBase):
    def __init__(self, session_provider: ISessionProvider,
                 session_name='sessionid',
                 cookie_max_age=None,
                 cookie_expires=None,
                 cookie_path="/",
                 cookie_domain=None,
                 cookie_secure=False,
                 cookie_samesite=None,
                 cookie_httponly=True
                 ):
        self.session_provider = session_provider
        self.session_name = session_name
        self.cookie_max_age = cookie_max_age
        self.cookie_expires = cookie_expires
        self.cookie_path = cookie_path
        self.cookie_domain = cookie_domain
        self.cookie_secure = cookie_secure
        self.cookie_samesite = cookie_samesite
        self.cookie_httponly = cookie_httponly

    def process_request(self, request, meta, **kwargs):
        context = AppContext.get(request.app_id)
        if context is None or self.session_provider is None:
            return

        """
        :type: HttpSession
        """
        key = md5.hash_str(b64.enc_bytes('%s#%s#%s' % (
            request.remote_addr, str(request.user_agent), context.app_id
        )))
        app_id = [ord(ch) for ch in list(context.app_id)]

        new_session_id = _encrypt_session_id(key, app_id)

        # 只要 cookie 中没有 session_id 那么就新建一个 session
        if self.session_name not in request.cookies:
            request.session = self.session_provider.create(new_session_id)
            return

        # noinspection PyBroadException
        try:
            old_session_id = request.cookies[self.session_name]
            cookie_key = _decrypt_session_id(old_session_id, app_id)
        except Exception as e:
            context.logger.warning('Cannot decode session id from cookie: %s' % repr(e))
            request.session = self.session_provider.create(new_session_id)
            return

        # 校验 session_id 合法性
        if key != cookie_key:
            context.logger.warning('Invalid session key: expected "%s", got "%s"' % (
                new_session_id, cookie_key))
            request.session = self.session_provider.create(new_session_id)
            return
        request.session = self.session_provider.get(old_session_id)

        # session 已经过期或session被清除
        if request.session is None:
            request.session = self.session_provider.create(new_session_id)
            return

        now = time.time()
        # session 过期
        if self.session_provider.is_expired(request.session):
            request.session = self.session_provider.create(new_session_id)
            return

        request.session.last_access_time = now

    def process_invoke(self, request, meta, **kwargs):
        pass

    def process_return(self, request, meta, data, **kwargs):
        pass

    def process_response(self, request, meta, response, **kwargs):
        # 在响应结束时才写入，以减少 IO
        if not request.session:
            return
        request.session.flush()
        response.set_cookie(self.session_name,
                            request.session.id,
                            max_age=self.cookie_max_age,
                            expires=self.cookie_expires,
                            path=self.cookie_path,
                            domain=self.cookie_domain,
                            secure=self.cookie_secure,
                            httponly=self.cookie_httponly,
                            samesite=self.cookie_samesite,
                            )

    def __del__(self):
        del self.session_provider
