import time

from restfx import __meta__
from restfx.middleware import MiddlewareBase


class TimetickMiddleware(MiddlewareBase):
    def __init__(self):
        self.route_time = __meta__.name + '-0-route-duration'
        self.invoke_time = __meta__.name + '-1-invoke-duration'
        self.response_time = __meta__.name + '-2-response-duration'

    def process_request(self, request, meta, **kwargs):
        request.timetick = {
            'request': time.time() * 1000
        }

    def process_invoke(self, request, meta, **kwargs):
        if request.timetick:
            request.timetick['invoke'] = time.time() * 1000

    def process_return(self, request, meta, data, **kwargs):
        if request.timetick:
            request.timetick['return'] = time.time() * 1000

    def process_response(self, request, meta, response, **kwargs):
        if not request.timetick:
            return

        request.timetick['response'] = time.time() * 1000

        response.headers.set(self.route_time, self._get_time(request, 'request', 'invoke'))
        response.headers.set(self.invoke_time, self._get_time(request, 'invoke', 'return'))
        response.headers.set(self.response_time, self._get_time(request, 'return', 'response'))

    @staticmethod
    def _get_time(request, from_, to):
        if from_ not in request.timetick or to not in request.timetick:
            return '0ms'
        return '%sms' % (request.timetick[to] - request.timetick[from_])
