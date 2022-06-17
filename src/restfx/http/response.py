import json
from io import BytesIO, IOBase
from typing import Tuple, Union

from werkzeug.exceptions import InternalServerError
from werkzeug.wrappers import Response


class HttpResponse(Response):
    def __init__(self, content=None, content_type='text/html;charset=utf-8',
                 status=200, headers=None, **kwargs):
        super().__init__(content, content_type=content_type, status=status,
                         headers=headers, **kwargs)


class JsonResponse(HttpResponse):
    def __init__(self, obj, encoder=None, content_type='application/json;charset=utf-8',
                 ensure_ascii=True, **kwargs):
        content = json.dumps(obj, ensure_ascii=ensure_ascii, cls=encoder)
        super().__init__(content, content_type=content_type, **kwargs)


class FileResponse(HttpResponse):
    def __init__(self, fp: Union[str, bytes, IOBase], attachment: [str, bool] = None,
                 content_type=None,
                 ranges: Tuple[int, int] = (),
                 request=None, **kwargs):
        """

        :param fp: 文件名或内容。如果指定的 fp 是文件名（字符串），那么认为传入的是文件名。
        :param attachment: 指定一个字符串，作为返回附件的文件名，当指定为 True （同时 fp 为文件名）时，将 fp 文件名作为 attachment 的值
        :param content_type: 当未指定此值时，如果指定的 fp 是文件名，那么会自动根据文件的扩展名进行识别
        :param ranges: 用于指定返回数据的分块起始位置
        :param kwargs:
        """
        # 如果是字符串，就认为是文件路径
        if isinstance(fp, str):
            if isinstance(attachment, bool) and attachment:
                from os import path
                attachment = path.basename(fp)
            # 根据文件的扩展名自动识别 mime
            if content_type is None:
                import mimetypes
                (content_type, _) = mimetypes.guess_type(fp)
            self.fp = open(fp, mode='rb')
        elif isinstance(fp, bytes):
            self.fp = BytesIO(fp)
        else:
            self.fp = fp

        if content_type is None:
            content_type = 'application/octet-stream'

        # 需要分块返回文件
        if ranges:
            # fix https://gitee.com/wangankeji/restfx/issues/I3SBXR
            # IOBase for BufferedReader(with open(xxx)) and BytesIO, etc.
            if not isinstance(self.fp, IOBase):
                raise TypeError('FileResponse with "ranges" works with type "IOBase" only')
            if not self._get_file_chunk(ranges, kwargs):
                super(FileResponse, self).__init__(status=416)
                return
            status_code = 206
        else:
            # fix https://gitee.com/wangankeji/restfx/issues/I3UN41
            headers = kwargs.get('headers')
            if headers is None:
                headers = {}
                kwargs['headers'] = headers
            if 'content-length' not in headers:
                headers['Content-Length'] = str(self._get_file_size())
            status_code = 200

        if attachment:
            self._set_attachment_header(request, attachment, kwargs)

        super().__init__(self.fp, status=status_code, direct_passthrough=True,
                         content_type=content_type, **kwargs)

    def _get_file_size(self):
        pos = self.fp.tell()
        self.fp.seek(0, 2)
        file_size = self.fp.tell()
        self.fp.seek(pos, 0)

        return file_size

    def _get_file_chunk(self, ranges: Tuple[int, int], kwargs):
        from io import BytesIO

        file_size = self._get_file_size()

        start, end = ranges

        if start >= file_size or end >= file_size:
            return False

        if end == 0:
            # 结束为 0 表示仅返回长度，而不返回内容
            self.fp = BytesIO()
            chunk_size = file_size
        else:
            chunk = BytesIO()
            # The fetched data size
            chunk_size = end - start
            self.fp.seek(start)
            buffer = self.fp.read(chunk_size)
            self.fp.close()
            chunk.write(buffer)
            chunk.seek(0)
            self.fp = chunk

        # set the response headers
        headers = kwargs.get('headers')
        if headers is None:
            headers = {}
            kwargs['headers'] = headers

        headers['Accept-Ranges'] = 'bytes'
        headers['Content-Length'] = str(chunk_size)
        headers['Content-Range'] = 'bytes %s-%s/%s' % (start, end, file_size)
        return True

    # noinspection PyMethodMayBeStatic
    def _set_attachment_header(self, request, filename, kwargs):
        from urllib.parse import unquote, quote

        headers = kwargs.get('headers')
        if headers is None:
            headers = {}
            kwargs['headers'] = headers

        if not request:
            from ..util import Logger
            Logger.current().warning(
                'You are using FileResponse for attachment,'
                'it is recommended to fill the "request" parameter.'
                'Otherwise, you may got an encoding issue of the filename on Firefox.'
            )

        user_agent = request and request.headers.environ['HTTP_USER_AGENT']
        is_firefox = user_agent and ('Firefox/' in user_agent)

        if is_firefox:
            from ..util import b64
            filename = '=?utf-8?B?' + b64.enc_bytes(unquote(filename).encode('utf-8')).decode() + '?='
        else:
            filename = quote(filename)

        headers['Content-Disposition'] = 'attachment;filename=%s' % filename


class BadRequest(HttpResponse):
    def __init__(self, content=None, **kwargs):
        super().__init__(content, status=400, **kwargs)


class Redirect(HttpResponse):
    def __init__(self, location, status=302, **kwargs):
        from markupsafe import escape
        super().__init__(None, status=status, headers={
            'Location': escape(location)
        }, **kwargs)


class Unauthorized(HttpResponse):
    def __init__(self, content=None, **kwargs):
        super().__init__(content, status=401, **kwargs)


class NotFound(HttpResponse):
    def __init__(self, content=None, **kwargs):
        super().__init__(content, status=404, **kwargs)


class ServerError(HttpResponse, InternalServerError):
    def __init__(self, content=None):
        if isinstance(content, Exception):
            content = content.args[0] if content.args else str(content)
        super().__init__(content, status=500, content_type='text/plain')
