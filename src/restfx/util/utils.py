import inspect


def load_module(module_name: str):
    """
    加载模块
    :param module_name:
    :return:
    """
    # __import__ 自带缓存
    module = __import__(module_name)
    temp = module_name.split('.')
    if len(temp) > 1:
        for seg in temp[1:]:
            module = getattr(module, seg)
    return module


def get_func_info(func):
    source_lines = inspect.getsourcelines(func)
    line = source_lines[1]
    return 'File "%s", line %d, in %s' % (
        inspect.getmodule(func).__file__,
        line,
        func.__name__
    )
