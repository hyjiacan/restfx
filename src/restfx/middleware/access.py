import logging
from typing import Tuple

from ..http import HttpRequest, HttpResponse
from . import MiddlewareBase


class StatusFilter:
    def __init__(self,
                 eq: int = None,
                 lt: int = None,
                 lte: int = None,
                 gt: int = None,
                 gte: int = None,
                 include: Tuple[int] = None,
                 exclude: Tuple[int] = None
                 ):
        self.eq = eq
        self.lt = lt
        self.lte = lte
        self.gt = gt
        self.gte = gte
        self.include = include
        self.exclude = exclude

    def set_eq(self, status: int):
        self.eq = status
        return self

    def set_lt(self, status: int):
        self.lt = status
        return self

    def set_lte(self, status: int):
        self.lte = status
        return self

    def set_gt(self, status: int):
        self.gt = status
        return self

    def set_gte(self, status: int):
        self.gte = status
        return self

    def set_include(self, status: Tuple[int]):
        self.include = status
        return self

    def set_exclude(self, status: Tuple[int]):
        self.exclude = status
        return self


class AccessMiddleware(MiddlewareBase):
    def __init__(self, logger_name: str = 'restfx', status_filter: StatusFilter = None):
        self.logger_name = logger_name
        self.logger = logging.getLogger(self.logger_name)
        self.status_filter = status_filter or StatusFilter()

    def on_leaving(self, request: HttpRequest, response: HttpResponse):
        status = response.status_code

        status_filter = self.status_filter

        if status_filter.lt is not None:
            if status >= status_filter.lt:
                return
        if status_filter.lte is not None:
            if status > status_filter.lte:
                return
        if status_filter.gt is not None:
            if status <= status_filter.gt:
                return
        if status_filter.gte is not None:
            if status < status_filter.gte:
                return
        if status_filter.include is not None:
            if status not in status_filter.include:
                return
        if status_filter.exclude is not None:
            if status in status_filter.exclude:
                return

        log_tpl = '[access] {remote} "{method} {path}" {status} {{{length}}}'.format(
            remote=request.environ.get('REMOTE_ADDR'),
            method=request.method,
            path=request.path,
            status=status,
            length=response.content_length or '-'
        )

        if status >= 500:
            self.logger.error(log_tpl)
        elif status >= 400:
            self.logger.warning(log_tpl)
        else:
            self.logger.debug(log_tpl)
