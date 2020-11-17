from abc import ABC, abstractmethod

from ..http.response import HttpResponse
from ..routes.meta import RouteMeta


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class MiddlewareBase(ABC):
    """
    路由中间件基类
    """

    @abstractmethod
    def process_request(self, request, meta: RouteMeta, **kwargs):
        """
        对 request 对象进行预处理。一般用于请求的数据的解码，此时路由组件尚水进行请求数据的解析(B,P,G 尚不可用)
        :param request:
        :param meta:
        :return: 返回 HttpResponse 以终止请求，返回 False 以停止执行后续的中间件(表示访问未授权)，返回 None 或不返回任何值继续执行后续中间件
        """
        pass

    @abstractmethod
    def process_invoke(self, request, meta: RouteMeta, **kwargs):
        """
        在路由函数调用前，对其参数等进行处理，此时路由组件已经完成了请求数据的解析(B,P,G 已可用)
        此时可以对解析后的参数进行变更
        :param request:
        :param meta:
        :return: 返回 HttpResponse 以终止请求，返回 False 以停止执行后续的中间件(表示访问未授权)，返回 None 或不返回任何值继续执行后续中间件
        """
        pass

    @abstractmethod
    def process_return(self, request, meta: RouteMeta, **kwargs):
        """
        在路由函数调用后，对其返回值进行处理
        :param request:
        :param meta:
        :param kwargs: 始终会有一个 'data' 的项，表示路由返回的原始数据
        :return: 返回 HttpResponse 以终止执行，否则返回新的 数据
        """
        pass

    @abstractmethod
    def process_response(self, request, meta: RouteMeta, **kwargs) -> HttpResponse:
        """
        对 response 数据进行预处理。一般用于响应的数据的编码
        :param request:
        :param meta:
        :param kwargs: 始终会有一个 'response' 的项，表示路由返回的原始 HttpResponse
        :return: 无论何种情况，应该始终返回一个  HttpResponse
        :rtype: HttpResponse
        """
        pass
