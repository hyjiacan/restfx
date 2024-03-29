from restfx.middleware import MiddlewareBase


class MiddlewareA(MiddlewareBase):
    def process_request(self, request, meta):
        print('process_request A')
        request.inject(injection="injection value from middleware")

    def process_invoke(self, request, meta, args):
        print('process_invoke A')

    def process_return(self, request, meta, data):
        print('process_return A')
        return data

    def process_response(self, request, meta, response):
        print('process_response A')


class MiddlewareB(MiddlewareBase):
    def process_request(self, request, meta):
        print('process_request B --break')

        return {
            'breaking': 'data'
        }

    def process_invoke(self, request, meta, args):
        print('process_invoke B')

    def process_return(self, request, meta, data):
        print('process_return B')

    def process_response(self, request, meta, response):
        print('process_response B')


class MiddlewareC(MiddlewareBase):
    def process_request(self, request, meta):
        print('process_request C')

    def process_invoke(self, request, meta, args):
        print('process_invoke C')

    def process_return(self, request, meta, data):
        print('process_return C')

    def process_response(self, request, meta, response):
        print('process_response C')
