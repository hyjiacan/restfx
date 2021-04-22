import re
from typing import Union

from restfx.http import HttpFile


class DefaultValidators:
    @classmethod
    def range(cls, min_, max_, include_min, include_max, msg, param_name: str, args: dict):
        if not min_ and not max_:
            return True

        value = args.get(param_name)

        if isinstance(value, (tuple, list, str)):
            temp = len(value)
        elif isinstance(value, HttpFile):
            temp = value.size
        elif value is None:
            # 值为 None 时，认为其长度为0（或者值为0）
            temp = 0
        else:
            temp = value

        if include_min and include_max:
            result = min_ <= temp <= max_
        elif include_min:
            result = min_ <= temp < max_
        else:
            result = min_ < temp <= max_

        return None if result else msg

    @classmethod
    def enums(cls, enums, msg, param_name: str, args: dict):
        value = args.get(param_name)
        return None if value in enums else msg

    @classmethod
    def match(cls, other_param_name, msg, param_name: str, args: dict):
        value = args.get(param_name)
        other_value = args.get(other_param_name)
        return None if value == other_value else msg

    @classmethod
    def regex(cls, pattern, flags, msg, param_name: str, args: dict):
        import re
        value = args.get(param_name)
        expr = re.compile(pattern, flags)
        return None if expr.fullmatch(value) else msg

    @classmethod
    def file(cls, file_ext, file_mime, msg, param_name: str, args: dict):
        value = args.get(param_name)
        """
        :type: HttpFile
        """
        if file_ext:
            if not value.filename.lower().endswith(file_ext.lower().split(';')):
                return msg
        if file_mime:
            if not value.mimetype.lower().endswith(file_mime.lower().split(';')):
                return msg
        return None


class Validator:
    """
    校验描述器，目前支持对 str, int, float, tuple, list, HttpFile 进行校验

    如果需要自定义校验器，那么请继承此类，添加自定义的方法即可

    在自定义的方法中，需要调用self._append_rule() 方法，以将自定义的校验加入到校验链中
    
    注意：自定义的方法必须返回 self，以支持链式调用
    """

    def __init__(self, param_name: str):
        self._param_name = param_name
        # 其内存储的项类型为 tuple 仅包含两项
        # 项的第一个值为 校验函数对象
        # 项的第二个值为 校验函数参数 (tuple)
        self._rule_chain = []
        """
        :type: List[Tuple(FunctionType, tuple)]
        """

    def _append_rule(self, val_fn, val_args: tuple):
        """
        向校验链中追加校验
        :param val_fn:
        :param val_args:
        :return:
        """
        self._rule_chain.append((val_fn, val_args))

    def range(self, min_: Union[int, float] = 0, max_: Union[int, float] = 0,
              include_min=True, include_max=True, msg='Value out of range'):
        """
        用于限制 字符串的长度 以及 int/float 的值范围

        若 min 和 max 都为 0, 那么表示不限制

        若都不为 0 ，表示限制输入数值范围或字符串长度

        当仅指定了 min 时，表示仅限制最小值/最小长度

        当仅指定了 最大值 时，表示仅限制最大值/最大长度

        在校验时，会包含端点值
        :param min_:
        :param max_:
        :param include_min: 是否包含最小值
        :param include_max: 是否包含最大值
        :param msg: 校验失败时的提示消息
        :return:
        """
        if min_ or max_:
            self._append_rule(DefaultValidators.range, (min_, max_, include_min, include_max, msg))
        return self

    def enum(self, enums: tuple, msg='Value out of range'):
        """
        用于指定允许可以使用的值
        :param enums:
        :param msg:
        :return:
        """
        if enums:
            self._append_rule(DefaultValidators.enums, (enums, msg))
        return self

    def regex(self, pattern: str = None, flags=0, msg='Invalid Value'):
        """
        仅应对字符串生效
        :param pattern:
        :param flags:
        :param msg:
        :return:
        """
        if pattern:
            self._append_rule(DefaultValidators.regex, (pattern, flags, msg))
        return self

    def ip(self, v4=True, v6=False, msg='Not a valid IP address'):
        """

        :param v4: 判断是否为 IPv4
        :param v6: 判断是否为 IPv6。保留参数，暂不支持
        :param msg:
        :return:
        """
        if v4:
            pattern = r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$'
        elif v6:
            pattern = None
        else:
            return self

        flags = 0
        self._append_rule(DefaultValidators.regex, (pattern, flags, msg))
        return self

    def email(self, msg='Not a valid Email'):
        pattern = r'^([a-z0-9_.-]+)@([\da-z.-]+)\.([a-z.]{2,6})$'
        flags = re.IGNORECASE
        self._append_rule(DefaultValidators.regex, (pattern, flags, msg))
        return self

    def match(self, other_param_name: str, msg='The two value not match'):
        """
        判断两个参数的值相同

        支持基本类型的比较：int float bool str list tuple dict
        :param other_param_name:
        :param msg:
        :return:
        """
        self._append_rule(DefaultValidators.match, (other_param_name, msg))
        return self

    def file(self, ext=None, mime=None, msg='Invalid file type'):
        """
        校验文件类型
        :param ext: 指定文件的扩展名，多个使用 ; 分隔
        :param mime: 指定文件的 mime，多个使用 ; 分隔
        :param msg:
        :return:
        """
        if ext or mime:
            self._append_rule(DefaultValidators.file, (ext, mime, msg))
        return self

    def validate(self, args: dict):
        """
        执行参数校验。
        :param args:
        :return: 返回 None 表示校验通过，返回字符串为校验失败的消息
        """
        common_args = [self._param_name, args]
        for fn, pre_args in self._rule_chain:
            result = fn(*pre_args, *common_args)
            if result is not None:
                return result

        return None

    def __str__(self):
        return '<V %s=%s>' % (self._param_name, ','.join([
            '%s(%s)' % (rule.func.__name__, ','.join([str(i) for i in rule.args]))
            for rule in self._rule_chain
        ]))
