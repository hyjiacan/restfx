import inspect
import re
from collections import OrderedDict

from ..base.request import HttpRequest
from ..routes.argument_specification import ArgumentSpecification


def get_func_docs(func):
    docs = {}

    # :type str
    doc_str = func.__doc__
    if doc_str is None:
        return docs

    temp = doc_str.splitlines(False)

    for row in temp:
        if not row:
            continue
        match = re.match(r'\s*:param\s+(?P<name>[\S]+):(?P<comment>.*)$', row)
        if not match:
            continue
        docs[match.group('name')] = match.group('comment')

    return docs


def get_func_args(func, logger):
    """
    获取函数的参数列表（带参数类型）
    :param logger:
    :param func:
    :return:
    """
    signature = inspect.signature(func)
    parameters = signature.parameters
    _empty = signature.empty

    documatation = get_func_docs(func)

    args = OrderedDict()
    index = 0
    for p in parameters.keys():
        parameter = parameters.get(p)
        spec = ArgumentSpecification(p, index)
        spec.is_variable = parameter.kind == parameter.VAR_KEYWORD

        if p in documatation:
            spec.comment = documatation[p]

        index += 1
        # 类型
        annotation = parameter.annotation

        # 无效的类型声明
        if not inspect.isclass(annotation):
            source_lines = inspect.getsourcelines(func)
            line = source_lines[1]
            row = None
            for row in source_lines[0]:
                if parameter.name in row:
                    break
                line += 1
            msg = 'File "%s", line %d, in %s\n\t' % (
                inspect.getmodule(func).__file__,
                line,
                func.__name__
            )
            msg += 'Invalid type declaration for argument "%s":\n\t\t%s'
            # abort the execution
            logger.error(msg % (parameter.name, row.strip()))

        default = parameter.default

        if default != _empty:
            spec.default = default
            spec.has_default = True

        # 有默认值时，若未指定类型，则使用默认值的类型
        if annotation == _empty:
            if default is not None and default != _empty:
                spec.annotation = type(default)
                spec.has_annotation = True
            elif p == 'request':
                # 以下情况将设置为 HttpRequest 对象
                # 1. 当参数名称是 request 并且未指定类型
                # 2. 当参数类型是 HttpRequest 时 (不论参数名称，包括 request)
                # 但是，参数名称是 request 但其类型不是 HttpRequest ，就会被当作一般参数处理
                spec.annotation = HttpRequest
                spec.has_annotation = True
        else:
            spec.annotation = annotation
            spec.has_annotation = True

        args[p] = spec

    return args


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
