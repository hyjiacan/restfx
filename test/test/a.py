from autorest import route
from autorest.base.request import HttpRequest


@route('测试', 'get')
def get(request: HttpRequest, foo: str, required_: int):
    """
    GET 测试
    :param request:
    :param foo: 请求的参数
    :return: 返回 get 请求的值
    :rtype: dict
    """
    session = request.session
    last_foo = None
    if session.has('foo'):
        last_foo = session.get('foo')
        # session.clear()
    session.set('foo', foo)
    return {
        'method': 'get',
        'foo': foo,
        'last-foo': last_foo,
        'required': required_
    }


@route('测试', 'get')
def post(request: HttpRequest, foo: str, bar=5, **kwargs):
    """
    POST 测试
    :param bar:
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
