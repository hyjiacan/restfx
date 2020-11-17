class Logger:
    def __init__(self, debug_mode: bool):
        self.debug_mode = debug_mode
        self.custom_logger = None

    def on_debug_mode_changed(self, debug_mode: bool):
        self.debug_mode = debug_mode

    def log(self, level, message, e=None):
        if self.custom_logger is None:
            print('[%s] %s' % (level, message))
        else:
            # noinspection PyUnresolvedReferences
            self.custom_logger(level, message, e)

    def debug(self, message):
        self.log('debug', message)

    def success(self, message):
        self.log('success', message)

    def info(self, message):
        self.log('info', message)

    def warning(self, message):
        self.log('warning', message)

    def error(self, message, e=None, _raise=True):
        temp = message if e is None else '%s\n\t%s' % (message, repr(e))

        # 非开发模式时，始终不会输出堆栈信息
        if not self.debug_mode:
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
