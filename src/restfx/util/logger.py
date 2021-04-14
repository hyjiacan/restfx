from logging import getLogger

from restfx import __meta__
from restfx.util import utils

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

    def error(self, message, e=None, _raise=True):
        temp = utils.get_exception_info(message, e)

        # 非开发模式时，始终不会输出堆栈信息
        if not self.debug:
            self.log('error', temp, e)
            return

        # print('\033[1;31;47m {0} \033[0m'.format(temp))
        # if e is not None:
        #     print(repr(e.__traceback__.tb_frame))

        # 不需要抛出异常
        if not _raise:
            self.log('error', temp, e)
            return

        # 抛出新的异常
        if e is None:
            raise Exception(message)

        # 修改异常消息
        # new_msg = '%s\n\t%s' % (temp, e.args[0]) if len(e.args) > 0 else temp
        e.args = (temp,)
        e.msg = temp
        raise e

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
