import time
import uuid

from ...config import AppConfig
from ...middleware.interface import MiddlewareBase
from ...session.interfaces import ISessionProvider
from ...util import md5, b64


class SessionMiddleware(MiddlewareBase):
    def __init__(self, provider: ISessionProvider,
                 secret=None,
                 maker=None,
                 cookie_name='sessionid',
                 cookie_max_age=None,
                 cookie_expires=None,
                 cookie_path="/",
                 cookie_domain=None,
                 cookie_secure=False,
                 cookie_samesite=None,
                 cookie_httponly=True
                 ):
        """

        :param provider:
        :param secret: 用于加密 session id 的密钥，设置为 None 时，将使用 app_id
        :param maker:session id 的创建算法:
            设置为 None 时表示使用默认的加密算法
            设置为函数表示自定义算法
        :param cookie_name:
        :param cookie_max_age:
        :param cookie_expires:
        :param cookie_path:
        :param cookie_domain:
        :param cookie_secure:
        :param cookie_samesite:
        :param cookie_httponly:
        """
        assert isinstance(provider, ISessionProvider)
        self.maker = maker
        self.secret = secret
        self.secret_bytes = None
        self.provider = provider
        self.cookie_name = cookie_name
        self.cookie_max_age = cookie_max_age
        self.cookie_expires = cookie_expires
        self.cookie_path = cookie_path
        self.cookie_domain = cookie_domain
        self.cookie_secure = cookie_secure
        self.cookie_samesite = cookie_samesite
        self.cookie_httponly = cookie_httponly

    @staticmethod
    def default_maker():
        return uuid.uuid4().hex

    def new_sid(self, request):
        sid = self.maker(request) if self.maker else self.default_maker()
        return md5.hash_str(sid)

    def decode(self, sid):
        """
        将客户端传过来的 sid 解码，取出其中的信息
        :param sid:
        :return:
        """
        # noinspection PyBroadException
        try:
            # 前端传来的 sid 是经过 base64 编码的
            sid_bytes = b64.dec_bytes(sid)
            # 使用 secret 解密
            result = bytearray()
            for i in range(32):
                result.append(sid_bytes[i] ^ self.secret_bytes[i])

            # 解密后能得到原始的 md5
            return result.decode()
        except Exception:
            # 解码失败，此 id 非法
            return None

    def on_startup(self, app):
        if self.secret is None:
            self.secret = app.id
        self.secret_bytes = md5.hash_str(self.secret).encode()

    def on_coming(self, request):
        config = AppConfig.current()
        if config is None or self.provider is None:
            return

        client_session_id = request.cookies.get(self.cookie_name)
        # 客户端无 session_id
        if not client_session_id:
            request.session = self.provider.create(self.new_sid(request))
            return

        # 解码 session_id
        session_id = self.decode(client_session_id)
        if not session_id:
            # session id 非法，新创建一个
            request.session = self.provider.create(self.new_sid(request))
            return

        # 尝试根据客户端的 session_id 获取 session
        request.session = self.provider.get(session_id)

        # session 已经过期或session被清除
        if request.session is None:
            request.session = self.provider.create(self.new_sid(request))
            return

        now = time.time()
        # session 过期
        if self.provider.is_expired(request.session):
            request.session = self.provider.create(self.new_sid(request))
            return

        # 修改已经存在 session 的最后访问时间
        request.session.last_access_time = now

    def on_leaving(self, request, response):
        # 在响应结束时才写入，以减少 IO
        if not request.session:
            return
        request.session.flush()
        # 使用 secret 加密
        sid_bytes = request.session.id.encode()
        result = bytearray()
        for i in range(32):
            result.append(sid_bytes[i] ^ self.secret_bytes[i])
        # 加密后的 sid
        sid = b64.enc_str(result)
        response.set_cookie(self.cookie_name,
                            sid,
                            max_age=self.cookie_max_age,
                            expires=self.cookie_expires,
                            path=self.cookie_path,
                            domain=self.cookie_domain,
                            secure=self.cookie_secure,
                            httponly=self.cookie_httponly,
                            samesite=self.cookie_samesite,
                            )

    def dispose(self):
        self.provider.dispose()
