import json

from restfx import IParam


class JsonType(IParam):
    """
    用于存储 dict 或者 list 类型的数据
    """

    @classmethod
    def parse(cls, value):
        if isinstance(value, (tuple, list, dict)):
            return value

        if not isinstance(value, str):
            raise Exception('Invalid data type "%s"' % type(value).__name__)

        if not value:
            return None

        if value[0] not in ('{', '[') or value[-1] not in ('}', ']'):
            raise Exception('Invalid JSON string')

        return json.loads(value)

    def __init__(self):
        self.data = None


__all__ = [
    'JsonType'
]
