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
