import time

from restfx.middleware import MiddlewareBase


class TimetickMiddleware(MiddlewareBase):
    """
    用于记录在路由的不同阶段的耗时情况
    """

    KEY = '__timetick__'
    HEADER = 'restfx-timetick'

    def __init__(self):
        pass

    def _get_timetick(self):
        return time.perf_counter() * 1000

    def on_coming(self, request):
        request.set(self.KEY, {
            'request': self._get_timetick()
        })

    def process_request(self, request, meta):
        timetick = request.get(self.KEY)
        if timetick:
            timetick['dispatch'] = self._get_timetick()

    def process_invoke(self, request, meta, args):
        timetick = request.get(self.KEY)
        if timetick:
            timetick['invoke'] = self._get_timetick()

    def process_return(self, request, meta, data):
        timetick = request.get(self.KEY)
        if timetick:
            timetick['return'] = self._get_timetick()

    def process_response(self, request, meta, response):
        timetick = request.get(self.KEY)
        if timetick:
            timetick['response'] = self._get_timetick()

    def on_leaving(self, request, response):
        total = self._get_time(request, 'request', 'response')
        rd = self._get_time(request, 'request', 'dispatch')
        dt = self._get_time(request, 'dispatch', 'invoke')
        it = self._get_time(request, 'invoke', 'return')
        rpt = self._get_time(request, 'return', 'response')

        response.headers[self.HEADER] = '%sms; 1/%sms, 2/%sms, 3/%sms, 4/%sms' % (
            total, rd, dt, it, rpt
        )

    @classmethod
    def _get_time(cls, request, from_, to):
        timetick = request.get(cls.KEY)
        if from_ not in timetick or to not in timetick:
            return 0
        return round(timetick[to] - timetick[from_], 3)
