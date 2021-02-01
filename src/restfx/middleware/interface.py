from abc import ABC, abstractmethod


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class MiddlewareBase(ABC):
    """
    路由中间件基类
    """

    def __int__(self, *args, **kwargs):
        pass

    def __del__(self):
        pass

    @abstractmethod
    def process_request(self, request, meta, **kwargs):
        """
        对 request 对象进行预处理。一般用于请求的数据的解码，此时路由组件尚水进行请求数据的解析(B,P,G 尚不可用)
        :param request:
        :type request: HttpRequest
        :param meta:
        :type meta: RouteMeta
        :return: 返回 HttpResponse 以终止请求，返回非 None 以停止执行后续的中间件，返回 None 或不返回任何值继续执行后续中间件
        """
        pass

    @abstractmethod
    def process_invoke(self, request, meta, **kwargs):
        """
        在路由函数调用前，对其参数等进行处理，此时路由组件已经完成了请求数据的解析(B,P,G 已可用)
        此时可以对解析后的参数进行变更
        :param request:
        :type request: HttpRequest
        :param meta:
        :type meta: RouteMeta
        :return: 返回 HttpResponse 以终止请求，返回非 None 以停止执行后续的中间件，返回 None 或不返回任何值继续执行后续中间件
        """
        pass

    @abstractmethod
    def process_return(self, request, meta, data, **kwargs):
        """
        在路由函数调用后，对其返回值进行处理
        :param request:
        :type request: HttpRequest
        :param meta:
        :type meta: RouteMeta
        :param data: 表示路由返回的原始数据
        :param kwargs: 保留参数
        :return: 返回 HttpResponse 以终止执行，否则返回新的数据
        """
        pass

    @abstractmethod
    def process_response(self, request, meta, response, **kwargs):
        """
        对 response 数据进行预处理。一般用于响应的数据的编码
        :param request:
        :type request: HttpRequest
        :param meta:
        :type meta: RouteMeta
        :param response: 表示路由返回的原始 HttpResponse
        :type response: HttpResponse
        :param kwargs: 始终会有一个 'response' 的项，
        :return: 返回类型可以是 HttpResponse 或 None(保留原来的 response)
        :rtype: Union[HttpResponse, None]
        """
        pass
