import inspect
import json
import re
from collections import OrderedDict
from enum import Enum
from types import FunctionType

from ..session import HttpSession
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
        # 是否是注入参数
        # 注入参数名称以 _ 开头
        self.is_injection = name[0] == '_'
        # 是否是可变参数
        self.is_variable = False
        # 是否有类型声明
        self.has_annotation = False
        # 是否有默认值
        self.has_default = False
        # 类型声明
        self.annotation = None
        # 类型是否是 tuple
        # 因为在处理类型时，会将 tuple 当作 list 对待
        self.is_tuple = False
        # 默认值
        self.default = None
        # 注释
        self.comment = None
        # 别名，当路由函数中声明的是 abc_def_xyz 时，自动处理为 abcDefXyz
        # 可能有多个
        self.alias = []
        # TODO 校验器
        self.validator = None

        if self.is_injection:
            return

        if '_' not in self.name:
            return

        # 同时会移除所有的 _ 符号
        alias = name.strip('_')
        if alias != name:
            self.alias.append(alias)
        alias = re.sub('_+(?P<ch>.?)', ArgumentSpecification._get_parameter_alias, name)
        if alias:
            self.alias.append(alias)

    def is_type(self, type_annotation: type, *extra_type_annotations: type):
        """
        判断此值是否属于指定的 ``type_annotation`` 或者 extra_type_annotations 指定的类型之一
        :param type_annotation:
        :param extra_type_annotations: 需要判断的其他类型
        :return:
        """
        if not extra_type_annotations:
            extra_type_annotations = (type_annotation,)
        else:
            extra_type_annotations = extra_type_annotations + (type_annotation,)

        for ta in extra_type_annotations:
            if not self.has_annotation:
                # 都为空
                if ta is None:
                    return True
                continue

            # 同一类型
            if self.annotation == ta:
                return True
            # 是子类
            if issubclass(self.annotation, ta):
                return True

        return False

    @property
    def annotation_name(self):
        return self.annotation.__name__ if self.has_annotation else None

    def __str__(self):
        name = self.name

        name = '%s/%s' % (name, '/'.join(self.alias)) if self.alias else name

        arg_type = self.annotation.__name__ if self.has_annotation else None

        if self.has_default:
            default_value = "'%s'" % self.default if isinstance(self.default, str) else self.default
            return '%s: %s=%s' % (name, arg_type, default_value)

        return '%s: %s' % (name, arg_type)

    class JSONEncoder(json.JSONEncoder):
        def default(self, o):
            if not isinstance(o, ArgumentSpecification):
                return json.JSONEncoder.default(self, o)
            return {
                'name': o.name,
                'index': o.index,
                'is_injection': o.is_injection,
                'is_variable': o.is_variable,
                'is_enum': o.is_type(Enum),
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
    node_iter = None
    """
    :type: NodeVisitor
    """

    def __init__(self, func: FunctionType):
        self.func = func
        self.description = ''
        self.return_description = ''
        self.return_type = ''
        self.arguments = self._get_args()
        self.decorator = None

    def _get_args(self):
        """
        获取函数的参数列表（带参数类型）
        :return:
        """
        signature = inspect.signature(self.func)
        parameters = signature.parameters
        _empty = signature.empty

        documentation = self._get_func_docs()

        self.description = documentation['__func__']
        self.return_type = documentation['__rtype__']
        self.return_description = documentation['__return__']

        args = OrderedDict()
        index = 0
        for p in parameters.keys():
            parameter = parameters.get(p)
            spec = ArgumentSpecification(p, index)

            spec.is_variable = parameter.kind == parameter.VAR_KEYWORD

            spec.comment = documentation.get(p)
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
                elif p == 'session':
                    # 以下情况将设置为 HttpSession 对象
                    # 1. 当参数名称是 session 并且未指定类型
                    # 2. 当参数类型是 HttpSession 时 (不论参数名称，包括 session)
                    # 但是，参数名称是 session 但其类型不是 HttpSession ，就会被当作一般参数处理
                    spec.annotation = HttpSession
                    spec.has_annotation = True
            else:
                spec.annotation = annotation
                spec.has_annotation = True

            # 如果声明的是元组，那么当成 list 来传
            if spec.has_annotation and spec.annotation == tuple:
                spec.annotation = list
                spec.is_tuple = True
            args[p] = spec

        return args

    def _get_func_docs(self):
        docs = {
            '__func__': '',
            '__return__': '',
            '__rtype__': None
        }

        # :type str
        doc_str = inspect.getdoc(self.func)
        if doc_str is None:
            return docs

        lines = doc_str.splitlines(False)

        buffer = []

        colon_found = False

        last_name = None

        for line in lines:
            if not line.startswith(':'):
                buffer.append(line)
                continue

            if not colon_found:
                docs['__func__'] = self.filter_doc_buffer(buffer)
                buffer.clear()
                colon_found = True

            if last_name:
                docs[last_name] = self.filter_doc_buffer(buffer)
                buffer.clear()
                last_name = None

            match = re.match(r':param\s+(?P<name>[\S]+):\s*(?P<comment>.*)$', line)

            if match:
                last_name = match.group('name')
                buffer.append(match.group('comment'))
                continue

            match = re.match(r':return:\s*(?P<comment>.*)$', line)

            if match:
                last_name = '__return__'
                buffer.append(match.group('comment'))
                continue

            match = re.match(r':rtype:\s*(?P<comment>.*)$', line)

            if match:
                last_name = '__rtype__'
                buffer.append(match.group('comment'))
                continue

        if last_name:
            docs[last_name] = self.filter_doc_buffer(buffer)
            buffer.clear()
        return docs

    @classmethod
    def filter_doc_buffer(cls, buffer):
        """
        移除注释中前置和后置的空行
        :param buffer:
        :return:
        """
        length = len(buffer)

        start = 0
        end = length

        data_range = range(length)

        for i in data_range:
            line = buffer[i].lstrip()
            if line:
                break
            start += 1

        if start == end:
            return ''

        for i in data_range:
            # 从尾部开始读取索引时，使用负数
            # 负数的索引应该从 -1 开始
            # i 的值从0 开始，所以 -i 需要 -1 才是尾部的索引
            line = buffer[-i - 1].lstrip()
            if line:
                break
            end -= 1

        temp = []
        # 提供代码段解析支持
        # 按缩进量处理
        found_code = False
        # 提供列表解析支持
        # 仅支持一级列表（无缩进）
        found_list = False
        buffer2 = []
        is_first_line = True
        last_line_is_blank = False
        first_indent = 0
        for line in buffer[start:end]:
            stripped_line = line.strip()
            indent = len(line) - len(line.lstrip())

            # 当前行有缩进 (>=2)，就表示其为代码段
            if indent >= 2 or ((found_code or found_list) and not stripped_line):
                if not stripped_line:
                    if last_line_is_blank:
                        found_code = False
                        found_list = False
                        continue
                    last_line_is_blank = True
                else:
                    last_line_is_blank = False
                is_first_line = False
                if not first_indent:
                    first_indent = indent

                if cls._is_list_item(stripped_line):
                    found_list = True
                elif not found_code:
                    # 重置临时数据
                    buffer2 = ['\n']
                    temp.append({
                        'type': 'code',
                        'lines': buffer2
                    })

                buffer2.append(line[first_indent:] + '\n')
                if not found_list:
                    found_code = True
                continue

            current_line_is_list_item = cls._is_list_item(stripped_line)
            if found_list and current_line_is_list_item == found_list:
                buffer2.append(stripped_line)
                continue
            else:
                found_list = current_line_is_list_item

            first_indent = 0
            if is_first_line:
                temp.append({
                    'type': found_list or 'text',
                    'lines': buffer2
                })
                is_first_line = False
            elif found_code:
                # 重置临时数据
                buffer2 = []
                temp.append({
                    'type': 'text',
                    'lines': buffer2
                })
            elif current_line_is_list_item:
                # 重置临时数据
                buffer2 = []
                temp.append({
                    'type': found_list,
                    'lines': buffer2
                })
            else:
                # 重置临时数据
                buffer2 = []
                temp.append({
                    'type': 'text',
                    'lines': buffer2
                })

            if stripped_line:
                if last_line_is_blank is True:
                    # 这个判断用于合并连续的多个空行为一个
                    buffer2.append('\n')
                    last_line_is_blank = False
                buffer2.append(line)
            elif found_code or found_list:
                # 忽略代码块后的第一个空行
                last_line_is_blank = True
            else:
                found_list = False

            found_code = False
        # return ''.join(temp)
        ol_re = re.compile(r'^\d+\.\s(.+?)$')
        for item in temp:
            type = item['type']
            lines = item['lines']
            # 处理 list 项的前缀
            if type == 'ul':
                item['lines'] = [i[2:] for i in lines]
            elif type == 'ol':
                item['lines'] = [ol_re.match(i).group(1) for i in lines]

        return temp

    @classmethod
    def _is_list_item(cls, line: str):
        # 无序
        if line.startswith('- '):
            return 'ul'
        if line.startswith('* '):
            return 'ul'
        # 有序
        if re.match(r'^\d+\.\s', line):
            return 'ol'

        return None

    class JSONEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, ArgumentSpecification):
                # noinspection PyCallByClass
                return ArgumentSpecification.JSONEncoder.default(self, o)
            if not isinstance(o, FunctionDescription):
                return json.JSONEncoder.default(self, o)
            return {
                'name': o.func.__name__,
                'description': o.description,
                'return_description': o.return_description,
                'return_type': o.return_type,
                'arguments': [o.arguments[arg] for arg in o.arguments]
            }
