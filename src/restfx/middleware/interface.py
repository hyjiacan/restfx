from abc import ABC


class MiddlewareBase(ABC):
    """
    路由中间件基类
    """

    def late_init(self, app):
        """
        在将此中间件实例传给 App.register_middleware() 后执行
        :param app: App 实例
        :return:
        """
        pass

    def process_request(self, request, meta):
        """
        对 request 对象进行预处理。一般用于请求的数据的解码，此时路由组件尚水进行请求数据的解析(BODY,POST,GET 尚不可用)
        :param request:
        :type request: HttpRequest
        :param meta:
        :type meta: RouteMeta
        :return: 返回 HttpResponse 以终止请求，返回非 None 以停止执行后续的中间件，返回 None 或不返回任何值继续执行后续中间件
        """
        pass

    def process_invoke(self, request, meta, args: dict):
        """
        在路由函数调用前，对其参数等进行处理，此时路由组件已经完成了请求数据的解析(BODY,POST,GET 已可用)
        此时可以对解析后的参数进行变更
        :param request:
        :type request: HttpRequest
        :param meta:
        :type meta: RouteMeta
        :param args: 调用路由函数时的实际参数，可以通过修改此参数来改变传给路由函数的参数
        :type args: dict
        :return: 返回 HttpResponse 以终止请求，返回非 None 以停止执行后续的中间件，返回 None 或不返回任何值继续执行后续中间件
        """
        pass

    def process_return(self, request, meta, data):
        """
        在路由函数调用后，对其返回值进行处理
        :param request:
        :type request: HttpRequest
        :param meta:
        :type meta: RouteMeta
        :param data: 表示路由返回的原始数据
        :return: 返回 HttpResponse 以终止执行，否则返回新的数据
        """
        pass

    def process_response(self, request, meta, response):
        """
        对 response 数据进行预处理。一般用于响应的数据的编码
        :param request:
        :type request: HttpRequest
        :param meta:
        :type meta: RouteMeta
        :param response: 表示路由返回的原始 HttpResponse
        :type response: HttpResponse
        :return: 返回类型可以是 HttpResponse 或 None(保留原来的 response)
        :rtype: Union[HttpResponse, None]
        """
        pass
