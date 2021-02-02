from werkzeug import Request
from werkzeug.datastructures import ImmutableDict, ImmutableMultiDict, FileStorage


def _get_request_data(data: ImmutableMultiDict) -> ImmutableDict:
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


class HttpRequest(Request):
    def __init__(self, environ, app_id: str):
        super().__init__(environ)
        self.app_id = app_id
        self.GET = _get_request_data(self.args)
        self.POST = _get_request_data(self.form)
        self.BODY = self.data
        self.FILES = self.files
        self.COOKIES = self.cookies
        self.session = None
        self.injections = {}

    def inject(self, **kwargs):
        self.injections.update(kwargs)


class HttpFile(FileStorage):
    pass
