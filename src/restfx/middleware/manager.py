from ..http.response import HttpResponse
from ..util import Logger, utils


class MiddlewareManager:
    """
    路由中间件管理器
    """

    def __init__(self, app_id: str, config):
        self.config = config
        self.logger = Logger.get(app_id)

    # def handle_startup(self, app):
    #     for middleware in self.config.middlewares:
    #         try:
    #             middleware.on_startup(app)
    #         except Exception as e:
    #             self.logger.error(utils.get_func_info(middleware.on_startup), e)
    #             break

    def handle_shutdown(self):
        for middleware in self.config.reversed_middlewares:
            try:
                middleware.on_shutdown()
            except Exception as e:
                self.logger.error(utils.get_func_info(middleware.on_shutdown), e)
                break

    def handle_coming(self, request):
        for middleware in self.config.middlewares:
            try:
                result = middleware.on_coming(request)
            except Exception as e:
                self.logger.error(utils.get_func_info(middleware.on_coming), e)
                break
            # 返回的值为 None，继续执行下一个中间件
            if result is None:
                continue
            # 返回其它类型，中止请求
            return result

    def handle_leaving(self, request, response):
        for middleware in self.config.reversed_middlewares:
            try:
                result = middleware.on_leaving(request, response)
            except Exception as e:
                self.logger.error(utils.get_func_info(middleware.on_leaving), e)
                break
            # 返回的值为 None，继续执行下一个中间件
            if result is None:
                continue
            # 返回其它类型，中止请求
            return result

    def handle_request(self, request, meta):
        for middleware in self.config.middlewares:
            try:
                result = middleware.process_request(request, meta)
            except Exception as e:
                self.logger.error(utils.get_func_info(middleware.process_request), e)
                break
            # 返回的值为 None，继续执行下一个中间件
            if result is None:
                continue
            # 返回其它类型，中止请求
            return result

    def before_invoke(self, request, meta, args: dict):
        """
        在路由函数调用前，对其参数等进行处理
        :return:
        """
        for middleware in self.config.middlewares:
            try:
                result = middleware.process_invoke(request, meta, args)
            except Exception as e:
                self.logger.error(utils.get_func_info(middleware.process_invoke), e)
                break
            # 返回的值为 None，继续执行下一个中间件
            if result is None:
                continue
            # 返回其它类型，中止请求
            return result

    def after_return(self, request, meta, data):
        """
        在路由函数调用后，对其返回值进行处理
        :return:
        """
        for middleware in self.config.reversed_middlewares:
            try:
                result = middleware.process_return(request, meta, data=data)
            except Exception as e:
                self.logger.error(utils.get_func_info(middleware.process_return), e)
                break
            # 返回的值为 None，继续执行下一个中间件
            if result is None:
                continue
            # 返回 HttpResponse，中止请求
            if isinstance(result, HttpResponse):
                return result
            # 使用返回值作为下一个中间件的数据
            data = result
        return data

    def handle_response(self, request, meta, response):
        """
        在响应前，对响应的数据进行处理
        :return:
        """
        # 对 response 进行处理
        for middleware in self.config.reversed_middlewares:
            try:
                result = middleware.process_response(request, meta, response=response)
            except Exception as e:
                self.logger.error(utils.get_func_info(middleware.process_response), e)
                break
            # 返回 None，那么继续执行下一个中间件
            if result is None:
                continue
            # 返回的是 HttpResponse，使用此值代替原来的值
            if isinstance(result, HttpResponse):
                response = result
                continue
            # 返回的不是 HttpResponse，返回的值类型不正确
            # 返回其它类型
            self.logger.warning('%s\n\tIgnored return type "%s", expect "None/HttpResponse"' % (
                utils.get_func_info(middleware.process_invoke), type(result).__name__
            ))

        return response
