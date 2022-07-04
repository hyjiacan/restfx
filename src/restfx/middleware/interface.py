from abc import ABC


class MiddlewareBase(ABC):
    """
    路由中间件基类
    """

    def force_run_method(self, method: int):
        """
        在执行中间件时，是否强制执行指定函数。
        指定类型的勾子函数，在前一个中间件返回了会阻止后续中间件继续执行的值时，仍会不爱影响地执行
        :param method: 来自 methods.on_coming, methods.process_request, ...的值
        :return: 返回 False 表示按默认逻辑跳过执行此中间件的指定函数，返回 True 表示仍然执行函数
        """
        return False

    def on_startup(self, app):
        """
        在注册中间件后立即调用
        :param app: App 实例
        :return: 不需要返回任何值
        """
        pass

    def on_shutdown(self):
        """
        在应用停止时调用
        :return:
        """
        pass

    def on_coming(self, request):
        """
        在收到请求时立即调用
        :param request:
        :return:
        返回 HttpResponse 以终止请求，
        返回 None 继续执行后续中间件，
        返回其它类型数据将作为请求的返回数据（会跳过路由调用）
        """
        pass

    def on_leaving(self, request, response):
        """
        在请求线束时调用，无论是否发生了异常
        :param request:
        :param response:
        :return:
        返回 HttpResponse 以终止请求，
        返回 None 继续执行后续中间件，
        返回其它类型数据将作为请求的返回数据（会跳过路由调用）
        """
        pass

    def process_request(self, request, meta):
        """
        对 request 对象进行预处理。一般用于请求的数据的解码，此时路由组件已经完成了请求数据的解析(BODY,POST,GET 已可用)
        :param request:
        :type request: HttpRequest
        :param meta:
        :type meta: RouteMeta
        :return:
        返回 HttpResponse 以终止请求，
        返回 None 继续执行后续中间件，
        返回其它类型数据将作为请求的返回数据（会跳过路由调用）
        """
        pass

    def process_invoke(self, request, meta, args: dict):
        """
        在路由函数调用前，对传递给路由函数参数等进行处理
        此时可以对解析后的参数进行变更
        :param request:
        :type request: HttpRequest
        :param meta:
        :type meta: RouteMeta
        :param args: 调用路由函数时的实际参数，可以通过修改此参数来改变传给路由函数的参数
        :type args: dict
        :return:
        返回 HttpResponse 以终止请求，
        返回 None 继续执行后续中间件，
        返回其它类型数据将作为请求的返回数据（会跳过路由调用）
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
        :return:
        返回 HttpResponse 以终止请求，
        返回非 None 时，其值作为下一个中间件的输入 data，
        返回 None 继续执行后续中间件
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
        :return:
        返回 HttpResponse 类型时，其值作为下一个中间件的输入 response，
        返回 None 继续执行后续中间件
        """
        pass

    def dispose(self):
        pass

