from restfx.middleware import MiddlewareBase


class MyMiddleware(MiddlewareBase):
    """
    自定义中间件。必须继承类 MiddlewareBase。
    方法 process_request,process_invoke,process_return,process_response
    按需要实现，不需要用到的可以不写（不用定义）。
    中间件的详细开发文档见：
    https://gitee.com/hyjiacan/restfx/wikis/07.%20%E4%B8%AD%E9%97%B4%E4%BB%B6%E7%B1%BB%E7%BB%93%E6%9E%84?sort_id=3533596
    """

    def on_startup(self, app):
        print('%s -> %s' % ('MyMiddleware', 'on_startup'))

    def on_shutdown(self):
        print('%s -> %s' % ('MyMiddleware', 'on_shutdown'))

    def process_request(self, request, meta):
        print('%s -> %s' % ('MyMiddleware', 'process_request'))

    def process_invoke(self, request, meta, args: dict):
        print('%s -> %s' % ('MyMiddleware', 'process_invoke'))

    def process_return(self, request, meta, data):
        print('%s -> %s' % ('MyMiddleware', 'process_return'))

    def process_response(self, request, meta, response):
        print('%s -> %s' % ('MyMiddleware', 'process_response'))
