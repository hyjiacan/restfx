import time

from restfx import __meta__
from restfx.middleware import MiddlewareBase


class TimetickMiddleware(MiddlewareBase):
    route_time = __meta__.name + '-duration-0-route'
    process_time = __meta__.name + '-duration-1-process'
    invoke_time = __meta__.name + '-duration-2-invoke'
    response_time = __meta__.name + '-duration-3-response'

    def __init__(self):
        pass

    def on_coming(self, request):
        request.timetick = {
            'request': time.perf_counter()
        }

    def process_request(self, request, meta):
        if request.timetick:
            request.timetick['dispatch'] = time.perf_counter()

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

        rd = self._get_time(request, 'request', 'dispatch')
        dt = self._get_time(request, 'dispatch', 'invoke')
        it = self._get_time(request, 'invoke', 'return')
        rpt = self._get_time(request, 'return', 'response')

        print('%s=%s\n%s=%s\n%s=%s\n%s=%s\n' % (
            self.route_time, rd,
            self.process_time, dt,
            self.invoke_time, it,
            self.response_time, rpt
        ))

        response.headers.set(self.route_time, rd)
        response.headers.set(self.process_time, dt)
        response.headers.set(self.invoke_time, it)
        response.headers.set(self.response_time, rpt)

    @staticmethod
    def _get_time(request, from_, to):
        if from_ not in request.timetick or to not in request.timetick:
            return '0ms'
        return '%sms' % ((request.timetick[to] - request.timetick[from_]) * 1000)
