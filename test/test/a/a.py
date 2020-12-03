from restfx import route
from restfx.http import HttpRequest


@route('模块名称', '第1个路由')
def get(request: HttpRequest, foo: str, required_: int):
    """
    GET 测试
    :param request:
    :param foo: 请求的参数
    :return: get 请求的值
    :rtype: dict
    """
    # session = request.session
    # last_foo = None
    # if session.has('foo'):
    #     last_foo = session.get('foo')
    #     # session.clear()
    # session.set('foo', foo)
    return {
        'method': 'get',
        'foo': foo,
        # 'last-foo': last_foo,
        'required': required_
    }


@route('模块名称', '第2个路由')
def post(request: HttpRequest, foo: list, bar=5, **kwargs):
    """
    POST 测试
    :param bar:
    :param request:
    :param foo: 请求的参数
    :return: post 请求的值
    :rtype: list
    """
    return True, ['post', foo, bar, kwargs]


@route('模块名称', '第3个路由')
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


@route('模块名称', '第4个路由')
def get_test():
    return {
        'test': True
    }
