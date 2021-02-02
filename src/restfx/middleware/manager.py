from ..context import AppContext
from ..http.response import HttpResponse
from ..routes.meta import RouteMeta


class MiddlewareManager:
    """
    路由中间件管理器
    """

    def __init__(self, request, meta: RouteMeta):
        self.context = AppContext.get(request.app_id)
        # HTTP请求对象
        self.request = request
        # 元数据信息
        self.meta = meta

    def handle_request(self):
        for middleware in self.context.middlewares:
            result = middleware.process_request(self.request, self.meta)
            if isinstance(result, HttpResponse):
                return result
            # 返回 None 以阻止后续中间件执行
            if result is not None:
                return result

    def before_invoke(self):
        """
        在路由函数调用前，对其参数等进行处理
        :return:
        """
        for middleware in self.context.middlewares:
            result = middleware.process_invoke(self.request, self.meta)
            if isinstance(result, HttpResponse):
                return result
            # 返回 None 以阻止后续中间件执行
            if result is not None:
                return result

    def after_return(self, data):
        """
        在路由函数调用后，对其返回值进行处理
        :param data:
        :return:
        """
        for middleware in self.context.reversed_middlwares:
            result = middleware.process_return(self.request, self.meta, data=data)

            # 返回 HttpResponse 终止
            if result is HttpResponse:
                return result

            if result is None:
                result = data

            # 使用原数据
            data = result

        return data

    def handle_response(self, response):
        """
        在响应前，对响应的数据进行处理
        :param response:
        :return:
        """
        # 对 response 进行处理
        for middleware in self.context.reversed_middlwares:
            new_response = middleware.process_response(self.request, self.meta, response=response)

            if new_response is not None:
                response = new_response

        return response
