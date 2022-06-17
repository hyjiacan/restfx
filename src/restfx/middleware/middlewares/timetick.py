import time

from .. import MiddlewareBase


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

    def force_run_method(self, method: int):
        return True

    def on_coming(self, request):
        request.set(self.KEY, [self._get_timetick()])

    def process_request(self, request, meta):
        request.get(self.KEY).append(self._get_timetick())

    def process_invoke(self, request, meta, args):
        request.get(self.KEY).append(self._get_timetick())

    def process_return(self, request, meta, data):
        request.get(self.KEY).append(self._get_timetick())

    def process_response(self, request, meta, response):
        request.get(self.KEY).append(self._get_timetick())

    def on_leaving(self, request, response):
        timetick = request.get(self.KEY)
        timetick.append(self._get_timetick())

        total = round(timetick[-1] - timetick[0], 3)
        detail = []
        i = 1
        prev = None
        for tt in timetick:
            if prev is not None:
                detail.append('%s/%sms' % (i, round(tt - prev, 3)))
                i += 1

            prev = tt

        response.headers[self.HEADER] = '%sms; %s' % (round(total, 3), ', '.join(detail))
