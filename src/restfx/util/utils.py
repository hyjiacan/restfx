import inspect


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
    return 'File "%s", line %d, in %s' % (
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


def get_exception_info(message: str, e: Exception = None):
    messages = [message]
    if e:
        tb = e.__traceback__

        while tb:
            msg = str(tb.tb_frame)
            # 移除前面的 '<frame at 0x0000016FE8839208, f' 字样
            # 和
            # 后面的 '>' 字样
            m = 'F' + msg[31:-1].replace('\\\\', '\\').replace("'", '"')
            messages.append(m)

            tb = tb.tb_next

        messages.append('\t' + str(e))

    return '\n\t'.join(messages)
