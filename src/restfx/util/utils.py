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
        # 此处的 line 是从 0 开始计算的，
        # 而在编辑器中，或者说从开发者角度来看，应该是从 1 开始计算
        # 所以 +1 以修正行号的正确性
        line + 1,
        func.__name__
    )
