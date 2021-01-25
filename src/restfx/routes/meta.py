from types import FunctionType


class RouteMeta:
    """
    路由元数据
    """

    def __init__(self,
                 handler: FunctionType,
                 func_args,
                 route_id=None,
                 module=None,
                 name=None,
                 extname=None,
                 method=None,
                 path=None,
                 kwargs=None):
        """

        :param handler: 路由处理函数对象
        :param func_args: 路由处理函数参数列表
        :param route_id: 路由ID，此ID由路由相关信息组合而成
        :param module: 装饰器上指定的 module 值
        :param name: 装饰器上指定的 name 值
        :param extname: 装饰器上指定的 name 值
        :param kwargs: 装饰器上指定的其它参数
        """
        self.handler = handler
        self.func_args = func_args
        self.id = route_id
        self.module = module
        self.name = name
        self.extname = extname
        self.method = method
        self.path = path
        self.kwargs = {} if kwargs is None else kwargs

    def has(self, arg_name):
        """
        指定的参数是否存在
        :param arg_name:
        :return:
        """
        return arg_name in self.kwargs

    def get(self, arg_name: str, default_value=None):
        """
        获取指定参数的值
        :param default_value:
        :param arg_name:
        :return:
        """
        return self.kwargs[arg_name] if arg_name in self.kwargs else default_value
