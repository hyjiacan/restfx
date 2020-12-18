from restfx.middleware import MiddlewareBase
from restfx.routes import RouteMeta


class MiddlewareA(MiddlewareBase):
    def process_request(self, request, meta: RouteMeta, **kwargs):
        print('process_request A')

    def process_invoke(self, request, meta: RouteMeta, **kwargs):
        print('process_invoke A')

    def process_return(self, request, meta: RouteMeta, **kwargs):
        print('process_return A')

    def process_response(self, request, meta: RouteMeta, **kwargs):
        print('process_response A')


class MiddlewareB(MiddlewareBase):
    def process_request(self, request, meta: RouteMeta, **kwargs):
        print('process_request B --break')

        return {
            'breaking': 'data'
        }

    def process_invoke(self, request, meta: RouteMeta, **kwargs):
        print('process_invoke B')

    def process_return(self, request, meta: RouteMeta, **kwargs):
        print('process_return B')

    def process_response(self, request, meta: RouteMeta, **kwargs):
        print('process_response B')


class MiddlewareC(MiddlewareBase):
    def process_request(self, request, meta: RouteMeta, **kwargs):
        print('process_request C')

    def process_invoke(self, request, meta: RouteMeta, **kwargs):
        print('process_invoke C')

    def process_return(self, request, meta: RouteMeta, **kwargs):
        print('process_return C')

    def process_response(self, request, meta: RouteMeta, **kwargs):
        print('process_response C')
