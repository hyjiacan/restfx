import inspect
import re
from typing import Type


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


def is_port_used(port):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('127.0.0.1', port))
        s.shutdown(2)
        return True
    except:
        return False


def get_enum_items(enum: Type):
    # 类型注释
    type_name = enum.__name__
    type_comment = inspect.getdoc(enum)
    source = inspect.getsource(enum)

    expr = r'([\S]+?)\s*=\s*(.+?)\s*\n\s*("""\n\s*(\S[\s\S]+?)\n\s*""")?'
    reg = re.compile(expr)
    matches = reg.findall(source)

    items = []
    for item in matches:
        items.append({
            'name': item[0],
            'value': item[1].strip("'").strip('"'),
            'comment': item[3]
        })

    return {
        'name': type_name,
        'comment': type_comment,
        'items': items
    }
