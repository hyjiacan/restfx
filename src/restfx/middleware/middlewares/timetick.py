import time

from restfx import __meta__
from restfx.middleware import MiddlewareBase


class TimetickMiddleware(MiddlewareBase):
    route_time = __meta__.name + '-0-route-duration'
    invoke_time = __meta__.name + '-1-invoke-duration'
    response_time = __meta__.name + '-2-response-duration'

    def __init__(self):
        pass

    @classmethod
    def on_requesting(cls, e):
        pass

    @classmethod
    def on_requested(cls, e):
        pass

    def late_init(self, app):
        app.on('requesting', self.on_requesting)

    def process_request(self, request, meta):
        request.timetick = {
            'request': time.perf_counter()
        }

    def process_invoke(self, request, meta, args):
        if request.timetick:
            request.timetick['invoke'] = time.perf_counter()

    def process_return(self, request, meta, data):
        if request.timetick:
            request.timetick['return'] = time.perf_counter()

    def process_response(self, request, meta, response):
        if not request.timetick:
            return

        request.timetick['response'] = time.perf_counter()

        rt = self._get_time(request, 'request', 'invoke')
        it = self._get_time(request, 'invoke', 'return')
        rpt = self._get_time(request, 'return', 'response')

        print('%s=%s, %s=%s, %s=%s' % (
            self.route_time, rt,
            self.invoke_time, it,
            self.response_time, rpt
        ))

        response.headers.set(self.route_time, rt)
        response.headers.set(self.invoke_time, it)
        response.headers.set(self.response_time, rpt)

    @staticmethod
    def _get_time(request, from_, to):
        if from_ not in request.timetick or to not in request.timetick:
            return '0ms'
        return '%sms' % ((request.timetick[to] - request.timetick[from_]) * 1000)
