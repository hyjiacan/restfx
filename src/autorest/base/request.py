from datetime import datetime

from werkzeug import Request

from ..base.app_context import AppContext
from ..util import utils


class HttpRequest(Request):
    def __init__(self, environ, context: AppContext):
        super().__init__(environ)
        self.context = context

        self.GET = self.args
        self.POST = self.form
        self.BODY = None
        self.FILES = self.files
        self.COOKIES = self.cookies

        # session id 构成：
        # remote_addr#user_agent#app_id
        expected_session_id = utils.str_md5(utils.base64_encode('%s#%s#%s' % (
            self.remote_addr, str(self.user_agent), context.app_id
        )))

        # 只要 cookie 中没有 session_id 那么就新建一个 session
        if context.sessionid_name not in self.cookies:
            self.session = context.session_provider.create(expected_session_id)
            return

        cookie_id = None
        # noinspection PyBroadException
        try:
            cookie_id = self.cookies[context.sessionid_name]
        except Exception as e:
            context.logger.warning('Cannot decode session id from cookie: %s' % repr(e))
            self.session = context.session_provider.create(expected_session_id)

        # 校验 session_id 合法性
        if expected_session_id != cookie_id:
            context.logger.warning('Invalid session_id: expected "%s", got "%s"' % (expected_session_id, cookie_id))
            self.session = context.session_provider.create(expected_session_id)
            return
        self.session = context.session_provider.get(expected_session_id)

        # session 已经过期
        if self.session is None:
            self.session = context.session_provider.create(expected_session_id)
            return

        self.session.last_access_time = datetime.now()
