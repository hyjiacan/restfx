from src.autorest import route, HttpRequest


@route('测试', 'get')
def get(request: HttpRequest, foo: str, required_: int):
    """
    GET 测试
    :param request:
    :param foo: 请求的参数
    :return: 返回 get 请求的值
    :rtype: dict
    """
    return {
        'method': 'get',
        'foo': foo,
        'required': required_
    }


@route('测试', 'get')
def post(request: HttpRequest, foo: str, bar=5, **kwargs):
    """
    POST 测试
    :param request:
    :param foo: 请求的参数
    :return: 返回 get 请求的值
    :rtype: dict
    """
    return {
        'method': 'post',
        'foo': foo,
        'bar': bar,
        **kwargs
    }


@route('测试', 'get')
def delete(request: HttpRequest, foo: str):
    """
    DELETE 测试
    :param request:
    :param foo: 请求的参数
    :return: 返回 get 请求的值
    :rtype: dict
    """
    return {
        'method': 'delete',
        'foo': foo
    }
