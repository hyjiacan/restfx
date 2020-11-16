import inspect
import json
import re
from collections import OrderedDict
from types import MethodType
from typing import OrderedDict as OrderedDictType

from .utils import get_func_info
from ..http import HttpRequest


class ArgumentSpecification:
    """
    函数参数声明
    """

    def __init__(self, name: str, index: int):
        """

        :param name: 参数名称
        :param index: 参数在参数位置中的位置
        """
        self.name = name
        self.index = index
        # 是否是可变参数
        self.is_variable = False
        # 是否有类型声明
        self.has_annotation = False
        # 是否有默认值
        self.has_default = False
        # 类型声明
        self.annotation = None
        # 默认值
        self.default = None
        # 注释
        self.comment = None
        # 别名，当路由处理函数中声明的是 abc_def 时，自动处理为 abcDef
        # 同时会移除所有的 _ 符号
        self.alias = re.sub('_+(?P<ch>.?)', ArgumentSpecification._get_parameter_alias, name)
        # 如果与原名称相同，那么就设置为 None 表示无别名
        if self.alias == name:
            self.alias = None

    @property
    def annotation_name(self):
        return self.annotation.__name__ if self.has_annotation else 'any'

    def __str__(self):
        arg_type = self.annotation.__name__ if self.has_annotation else 'any'

        name = self.name

        name = name if self.alias is None else '%s/%s' % (name, self.alias)

        if self.has_default:
            default_value = "'%s'" % self.default if isinstance(self.default, str) else self.default
            return '%s: %s=%s' % (name, arg_type, default_value)

        return '%s: %s' % (name, arg_type)

    class JsonEncoder(json.JSONEncoder):
        def default(self, o):
            if not isinstance(o, ArgumentSpecification):
                return json.JSONEncoder.default(self, o)
            return {
                'name': o.name,
                'index': o.index,
                'is_variable': o.is_variable,
                'has_annotation': o.has_annotation,
                'has_default': o.has_default,
                'default': o.default,
                'annotation_name': o.annotation_name,
                'comment': o.comment,
                'alias': o.alias
            }

    @staticmethod
    def _get_parameter_alias(match):
        """

        :param match:
        :type match: Match
        :return:
        """
        ch = match.group('ch')
        return '' if ch is None else ch.upper()


class FunctionDescription:
    def __init__(self, func: MethodType):
        self.func = func
        self.description = ''
        self.return_description = ''
        self.return_type = ''
        self.arguments = self._get_func_args()

    def _get_func_args(self) -> OrderedDictType[str, ArgumentSpecification]:
        """
        获取函数的参数列表（带参数类型）
        :return:
        """
        signature = inspect.signature(self.func)
        parameters = signature.parameters
        _empty = signature.empty

        documatation = self._get_func_docs()

        self.description = documatation['__func__']
        self.return_type = documatation['__rtype__']
        self.return_description = documatation['__return__']

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

            # 无效的类型声明 (意外的代码错误)
            if not inspect.isclass(annotation):
                source_lines = inspect.getsourcelines(self.func)
                line = source_lines[1]
                row = None
                for row in source_lines[0]:
                    if parameter.name in row:
                        break
                    line += 1
                msg = get_func_info(self.func)
                msg += 'Invalid type declaration for argument "%s":\n\t\t%s'
                # abort the execution
                raise Exception(msg % (parameter.name, row.strip()))

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

    def _get_func_docs(self):
        docs = {
            '__func__': '',
            '__return__': '',
            '__rtype__': None
        }

        # :type str
        doc_str = self.func.__doc__
        if doc_str is None:
            return docs

        lines = doc_str.splitlines(False)

        buffer = []

        colon_found = False

        last_name = None

        for line in lines:
            line = line.strip()

            if not line:
                continue

            if not line.startswith(':'):
                buffer.append(line)
                continue

            if not colon_found:
                docs['__func__'] = ' '.join(buffer)
                buffer.clear()
                colon_found = True
                continue

            if last_name:
                docs[last_name] = ' '.join(buffer)
                buffer.clear()
                last_name = None

            match = re.match(r':param\s+(?P<name>[\S]+):(?P<comment>.*)$', line)

            if match:
                last_name = match.group('name')
                buffer.append(match.group('comment'))
                continue

            match = re.match(r':return:(?P<comment>.*)$', line)

            if match:
                last_name = '__return__'
                buffer.append(match.group('comment'))
                continue

            match = re.match(r':rtype:(?P<comment>.*)$', line)

            if match:
                last_name = '__rtype__'
                buffer.append(match.group('comment'))
                continue

        if last_name:
            docs[last_name] = ' '.join(buffer)
            buffer.clear()
        return docs
