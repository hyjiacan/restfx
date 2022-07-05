import uuid

from werkzeug import Request
from werkzeug.datastructures import ImmutableDict, FileStorage, MultiDict

from ..globs import _request_ctx_stack, _app_ctx_stack
from ..session import HttpSession
from ..util import ContextStore


def _get_request_data(data: MultiDict) -> ImmutableDict:
    args = {}
    for key in data.keys():
        value = data.getlist(key)
        value_len = len(value)
        if not value_len:
            args[key] = None
            continue
        if value_len == 1:
            args[key] = value[0]
            continue
        args[key] = value
    return ImmutableDict(args)


def _get_files(files):
    result = {}
    if not files:
        return result

    for name in files:
        file = files.get(name)
        result[name] = HttpFile.inherit(file)

    return ImmutableDict(result)


class RequestContext:
    def __init__(self, request):
        self.request = request
        self.store = ContextStore(_request_ctx_stack)
        self.ref_count = 0

    @property
    def session(self) -> HttpSession:
        return self.request.session

    def push(self):
        top = _app_ctx_stack.top
        if not top or top != self.request.app:
            self.request.app.context.push()
        if _request_ctx_stack.top != self:
            _request_ctx_stack.push(self)
        self.ref_count += 1

    def pop(self):
        if _request_ctx_stack.top != self:
            return
        self.ref_count -= 1
        if self.ref_count > 0:
            return
        _request_ctx_stack.pop()
        del self.store

    def __enter__(self):
        self.push()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pop()


class HttpRequest(Request):
    def __init__(self, environ, app):
        super().__init__(environ)
        self.id = uuid.uuid4().hex
        self.app = app
        self.app_id = app.id
        self.GET = _get_request_data(self.args)
        self.POST = _get_request_data(self.form)
        self.BODY = self.data
        self.FILES = _get_files(self.files)
        self.COOKIES = self.cookies
        self.session = None
        """
        :type: HttpSession
        """
        self._injections = {}
        # 用于存放一些用户的数据
        self._user_data = {}
        # 在同一个请求中，使用同一个请求上下文
        self._ctx = RequestContext(self)

    def inject(self, **kwargs):
        self._injections.update(kwargs)

    def context(self, **kwargs):
        self._ctx.store.update(kwargs)
        return self._ctx

    def get(self, key: str, default=None):
        """
        读取附加到 request 上的自定义数据
        :param key:
        :param default:
        :return:
        """
        return self._user_data.get(key, default)

    def set(self, key: str, value):
        """
        设置附加到 request 上的自定义数据
        :param key:
        :param value:
        :return:
        """
        return self._user_data.setdefault(key, value)

    def remove(self, key: str):
        """
        移除附加到 request 上的自定义数据
        :param key:
        :return
        """
        return self._user_data.pop(key)

    @property
    def range(self):
        import re
        request_range = self.headers.get('range')
        if not request_range:
            return None
        match = re.fullmatch(r'\s*(?P<unit>(bytes))=(?P<start>([0-9]+))-(?P<end>([0-9]*))?\s*', request_range)
        if not match:
            from ..util import Logger
            from . import BadRequest
            Logger.current().warning('Invalid value of request header "range": %r' % request_range)
            return BadRequest()

        return match.group('unit'), int(match.group('start')), int(match.group('end') or 0)

    @staticmethod
    def current():
        """
        获取当前的请求对象
        :return:
        """
        from .. import globs
        return globs.request

    @staticmethod
    def store():
        """
        获取当前请求的存储对象
        :return:
        """
        from .. import globs
        return globs.req_store


class HttpFile(FileStorage):
    @property
    def size(self):
        """
        此功能处于试用阶段，尚未知晓其可能产生的副作用
        :return:
        """
        # noinspection PyBroadException
        try:
            position = self.stream.tell()
            self.stream.seek(0, 2)
            size = self.stream.tell()
            self.stream.seek(position, 0)
            return size
        except Exception:
            return self.content_length

    @staticmethod
    def inherit(file: FileStorage):
        return HttpFile(
            stream=file.stream,
            filename=file.filename,
            name=file.name,
            content_type=file.content_type,
            content_length=file.content_length,
            headers=file.headers
        )
