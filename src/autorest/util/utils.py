import base64
import hashlib
import inspect


def load_module(module_name: str):
    """
    加载模块
    :param module_name:
    :return:
    """
    # noinspection PyTypeChecker
    return __import__(module_name, fromlist=True)


def get_func_info(func):
    source_lines = inspect.getsourcelines(func)
    line = source_lines[1]
    return 'File "%s", line %d, in %s' % (
        inspect.getmodule(func).__file__,
        line,
        func.__name__
    )


def str_md5(s: str):
    return hashlib.md5(s.encode(encoding='utf8')).hexdigest()


def base64_encode(s: str) -> str:
    return base64.b64encode(s.encode(encoding='utf8')).decode()


def base64_decode(s: str) -> str:
    return base64.b64decode(s.encode()).decode('utf-8')
