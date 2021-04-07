import json

from werkzeug.exceptions import InternalServerError
from werkzeug.utils import escape
from werkzeug.wrappers import Response


class HttpResponse(Response):
    def __init__(self, content=None, content_type='text/html;charset=utf8',
                 status=200, headers=None, **kwargs):
        super().__init__(content, content_type=content_type, status=status,
                         headers=headers, **kwargs)


class JsonResponse(HttpResponse):
    def __init__(self, obj, encoder=None, content_type='application/json;charset=utf8',
                 ensure_ascii=True, **kwargs):
        content = json.dumps(obj, ensure_ascii=ensure_ascii, cls=encoder)
        super().__init__(content, content_type=content_type, **kwargs)


class FileResponse(HttpResponse):
    def __init__(self, fp, attachment: str = None, content_type='application/octet-stream',
                 request=None, **kwargs):
        """

        :param fp:
        :param attachment: 指定一个字符串，作为返回附件的文件名
        :param content_type:
        :param kwargs:
        """
        # 如果是字符串，就认为是文件路径
        if isinstance(fp, str):
            self.fp = open(fp, mode='rb')
        else:
            self.fp = fp

        if attachment:
            self._set_attachment_header(request, attachment, kwargs)

        super().__init__(self.fp, direct_passthrough=True, content_type=content_type, **kwargs)

    # noinspection PyMethodMayBeStatic
    def _set_attachment_header(self, request, filename, kwargs):
        from urllib.parse import unquote, quote

        headers = {}
        for name in kwargs:
            if name.lower() == 'headers':
                headers = kwargs[name]
                break

        if not headers:
            kwargs['headers'] = headers

        if not request:
            from ..util import Logger
            Logger.print('warning',
                         'You are using FileResponse for attachment,'
                         'it is recommended to fill the "request" parameter.'
                         'Otherwise, you may got an encoding issue of the filename.'
                         )

        user_agent = request and request.headers.environ['HTTP_USER_AGENT']
        is_firefox = user_agent and ('Firefox/' in user_agent)

        if is_firefox:
            from ..util import b64
            filename = '=?utf-8?B?' + b64.enc_bytes(unquote(filename).encode('utf-8')).decode() + '?='
        else:
            filename = quote(filename)

        headers['Content-Disposition'] = 'attachment;filename=%s' % filename


class HttpBadRequest(HttpResponse):
    def __init__(self, content=None, **kwargs):
        super().__init__(content, status=400, **kwargs)


class HttpRedirect(HttpResponse):
    def __init__(self, location, status=302, **kwargs):
        super().__init__(None, status=status, headers={
            'Location': escape(location)
        }, **kwargs)


class HttpUnauthorized(HttpResponse):
    def __init__(self, content=None, **kwargs):
        super().__init__(content, status=401, **kwargs)


class HttpNotFound(HttpResponse):
    def __init__(self, content=None, **kwargs):
        super().__init__(content, status=404, **kwargs)


class HttpServerError(HttpResponse, InternalServerError):
    def __init__(self, content=None):
        if isinstance(content, Exception):
            content = str(content)
        super().__init__(content, status=500, content_type='text/plain')
