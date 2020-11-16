from ..http.response import HttpResponse
from ..routes.meta import RouteMeta


class MiddlewareManager:
    """
    路由中间件管理器
    """

    def __init__(self, request, meta: RouteMeta):
        self.context = request.context
        # HTTP请求对象
        self.request = request
        # 元数据信息
        self.meta = meta

    def begin(self):
        for middleware in self.context.middlewares:
            if not hasattr(middleware, 'process_request'):
                continue
            result = middleware.process_request(self.request, self.meta)
            if isinstance(result, HttpResponse):
                return result
            # 返回 False 以阻止后续中间件执行
            if result is False:
                return

    def before_invoke(self):
        """
        在路由函数调用前，对其参数等进行处理
        :return:
        """
        for middleware in self.context.middlewares:
            if not hasattr(middleware, 'process_invoke'):
                continue
            result = middleware.process_invoke(self.request, self.meta)
            if isinstance(result, HttpResponse):
                return result
            # 返回 False 以阻止后续中间件执行
            if result is False:
                return

    def process_return(self, data):
        """
        在路由函数调用后，对其返回值进行处理
        :param data:
        :return:
        """
        for middleware in self.context.middlewares:
            if not hasattr(middleware, 'process_return'):
                continue
            result = middleware.process_return(self.request, self.meta, data=data)

            # 返回 HttpResponse 终止
            if result is HttpResponse:
                return result

            # 使用原数据
            data = result

        return data

    def end(self, response):
        """
        在响应前，对响应的数据进行处理
        :param response:
        :return:
        """
        # 对 response 进行处理
        for middleware in self.context.middlewares:
            if not hasattr(middleware, 'process_response'):
                continue
            response = middleware.process_response(self.request, self.meta, response=response)

        return response
