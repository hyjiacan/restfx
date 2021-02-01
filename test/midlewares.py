from restfx.middleware import MiddlewareBase


class MiddlewareA(MiddlewareBase):
    def process_request(self, request, meta, **kwargs):
        print('process_request A')
        request.inject(injection="injection value from middleware")

    def process_invoke(self, request, meta, **kwargs):
        print('process_invoke A')

    def process_return(self, request, meta, data, **kwargs):
        print('process_return A')

    def process_response(self, request, meta, response, **kwargs):
        print('process_response A')


class MiddlewareB(MiddlewareBase):
    def process_request(self, request, meta, **kwargs):
        print('process_request B --break')

        return {
            'breaking': 'data'
        }

    def process_invoke(self, request, meta, **kwargs):
        print('process_invoke B')

    def process_return(self, request, meta, data, **kwargs):
        print('process_return B')

    def process_response(self, request, meta, response, **kwargs):
        print('process_response B')


class MiddlewareC(MiddlewareBase):
    def process_request(self, request, meta, **kwargs):
        print('process_request C')

    def process_invoke(self, request, meta, **kwargs):
        print('process_invoke C')

    def process_return(self, request, meta, data, **kwargs):
        print('process_return C')

    def process_response(self, request, meta, response, **kwargs):
        print('process_response C')
