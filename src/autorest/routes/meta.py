from types import MethodType


class RouteMeta:
    """
    路由元数据
    """

    def __init__(self,
                 handler: MethodType,
                 func_args,
                 route_id=None,
                 module=None,
                 name=None,
                 kwargs=None):
        """

        :param handler: 路由处理函数对象
        :param func_args: 路由处理函数参数列表
        :param route_id: 路由ID，此ID由路由相关信息组合而成
        :param module: 装饰器上指定的 module 值
        :param name: 装饰器上指定的 name 值
        :param kwargs: 装饰器上指定的其它参数
        """
        self._handler = handler
        self._func_args = func_args
        self._id = route_id
        self._module = module
        self._name = name
        self._kwargs = {} if kwargs is None else kwargs

    @property
    def handler(self) -> MethodType:
        """
        路由处理函数对象
        :return:
        """
        return self._handler

    @property
    def func_args(self):
        """
        路由处理函数参数列表
        :return:
        :rtype: OrderedDict
        """
        return self._func_args

    @property
    def id(self) -> str:
        """
        路由ID，此ID由路由相关信息组合而成
        :return:
        """
        return self._id

    @property
    def module(self) -> str:
        """
        装饰器上指定的 module 值
        :return:
        """
        return self._module

    @property
    def name(self) -> str:
        """
        装饰器上指定的 name 值
        :return:
        """
        return self._name

    @property
    def kwargs(self) -> dict:
        """
        装饰器上指定的其它参数
        :return:
        :rtype: Dict
        """
        return self._kwargs

    def has(self, arg_name):
        """
        指定的参数是否存在
        :param arg_name:
        :return:
        """
        return arg_name in self._kwargs

    def get(self, arg_name: str, default_value=None):
        """
        获取指定参数的值
        :param default_value:
        :param arg_name:
        :return:
        """
        return self._kwargs[arg_name] if arg_name in self._kwargs else default_value
