from logging import getLogger

from .. import __meta__
from . import utils

logger = getLogger(__meta__.name)


class Logger:
    _LOGGERS = {}
    colors = {
        'error': '\033[1;31m',
        'warning': '\033[1;33m',
        'debug': '\033[1;37m'
    }

    def __init__(self, app_id: str):
        self.app_id = app_id
        self._LOGGERS[app_id] = self
        self.custom_logger = None

    @classmethod
    def print(cls, level, message):

        if level not in cls.colors:
            print('%s' % message)
            return

        print('%s%s%s' % (cls.colors[level], message, '\033[0m'))

    def log(self, level, message, e=None):
        if self.custom_logger is not None:
            # noinspection PyUnresolvedReferences
            self.custom_logger(level, message, e)
            return
        getattr(logger, level)(message)
        # self.print(level, message)

    def debug(self, message):
        self.log('debug', message)

    def info(self, message):
        self.log('info', message)

    def warning(self, message):
        self.log('warning', message)

    def error(self, message, e=None):
        if e:
            self.log('error', utils.get_exception_info(e, message + '\n' + repr(e)), e)
        else:
            self.log('error', message)

    @classmethod
    def remove(cls, app_id: str):
        if app_id in cls._LOGGERS:
            del cls._LOGGERS[app_id]

    @classmethod
    def get(cls, app_id: str):
        _logger = cls._LOGGERS.get(app_id, None)
        if _logger is None:
            _logger = Logger(app_id)
        return _logger

    @classmethod
    def current(cls):
        from .. import globs
        app_id = globs.current_app.id
        return cls.get(app_id)
