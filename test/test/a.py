from restfx import route
from restfx.http import HttpRequest


@route('测试', 'get')
def get(request: HttpRequest, foo: str, required_: int):
    """
    GET 测试
    :param request:
    :param foo: 请求的参数
    :return: get 请求的值
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


@route('测试', 'post')
def post(request: HttpRequest, foo: str, bar=5, **kwargs):
    """
    POST 测试
    :param bar:
    :param request:
    :param foo: 请求的参数
    :return: post 请求的值
    :rtype: list
    """
    return True, ['post', foo, bar, kwargs.values()]


@route('测试', 'delete')
def delete(request: HttpRequest, foo: str):
    """
    DELETE 测试
    :param request:
    :param foo: 请求的参数
    :return: delete 请求的值
    """
    return {
        'method': 'delete',
        'foo': foo
    }
