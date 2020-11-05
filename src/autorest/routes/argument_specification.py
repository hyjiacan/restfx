import json
import re


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
