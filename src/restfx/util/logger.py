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

    def log(self, level, message, e=None):
        if self.custom_logger is not None:
            # noinspection PyUnresolvedReferences
            self.custom_logger(level, message, e)
            return

        if level not in self.colors:
            print('[%s] %s' % (level, message))
            return

        print('%s[%s] %s%s' % (self.colors[level], level, message, '\033[0m'))

    def debug(self, message):
        self.log('debug', message)

    def info(self, message):
        self.log('info', message)

    def warning(self, message):
        self.log('warning', message)

    def error(self, message, e=None, _raise=True):
        temp = message if e is None else '%s\n\t%s' % (message, str(e))

        # 非开发模式时，始终不会输出堆栈信息
        if not self.debug:
            self.log('ERROR', temp, e)
            return

        # print('\033[1;31;47m {0} \033[0m'.format(temp))
        # if e is not None:
        #     print(repr(e.__traceback__.tb_frame))

        # 不需要抛出异常
        if not _raise:
            self.log('ERROR', temp, e)
            return

        # 抛出新的异常
        if e is None:
            raise Exception(message)

        # 修改异常消息
        new_msg = '%s\n\t%s' % (message, e.args[0]) if len(e.args) > 0 else message
        e.args = (new_msg,)
        raise e

    @classmethod
    def remove(cls, app_id: str):
        if app_id in cls._LOGGERS:
            del cls._LOGGERS[app_id]

    @classmethod
    def get(cls, app_id: str):
        logger = cls._LOGGERS.get(app_id, None)
        if logger is None:
            logger = Logger(app_id)
        return logger
