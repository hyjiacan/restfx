import inspect
import re


def load_module(module_name: str, level=0):
    """
    加载模块
    :param level:
    :param module_name:
    :return:
    """
    # __import__ 自带缓存
    module = __import__(module_name, level=level, globals={
        **globals(),
        **locals()
    })
    temp = module_name.split('.')
    if len(temp) > 1:
        for seg in temp[1:]:
            module = getattr(module, seg)
    return module


def get_func_info(func):
    source_lines = inspect.getsourcelines(func)
    line = source_lines[1]
    return 'File "%s", line %d, code %s' % (
        inspect.getmodule(func).__file__,
        line,
        func.__name__
    )


def get_ip_list():
    """
    读取本机的IP地址列表
    :return:
    """
    import socket

    addresses = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)

    ips = ['127.0.0.1']
    for address in addresses:
        ip = address[4][0]
        if ip not in ips:
            ips.append(ip)

    return ips


def get_exception_info(e: Exception, message: str = None):
    messages = []
    if e:
        tb = e.__traceback__

        while tb:
            msg = str(tb.tb_frame.f_code)
            match = re.match(r'^<code object (?P<name>(<module>|[a-zA-Z0-9_]+?)) at.+?, file (?P<file>(.+?)),.+$', msg)
            if match:
                msg = 'File %s, line %s, code %s' % (match.group('file'), tb.tb_frame.f_lineno, match.group('name'))
            messages.append(msg)

            tb = tb.tb_next

    if message:
        messages.append(message)
    else:
        messages.append(str(e))

    return '\n\t'.join(messages)
