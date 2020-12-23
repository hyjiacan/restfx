from restfx import route
from restfx.http import HttpRequest


@route(module='测试名称-模块', name='测试名称-GET')
def get(request, param1, param2=None, param3: int = 5):
    """

    :param request:
    :param param1:
    :param param2:
    :param param3:
    :return: 返回值为参数字典
    """
    # request 会是 HttpRequest
    return {
        'param1': param1,
        'param2': param2,
        'param3': param3,
    }


@route(module='测试名称-模块', name='测试名称-POST_PARAM')
def get_param(param1, req: HttpRequest, from_=None, param3=5):
    """

    :param param1:
    :param req:
    :param from_:
    :param param3:
    :return: 返回值为参数字典
    """
    # req 会是 HttpRequest
    return {
        'param1': param1,
        'from': from_,
        'param3': param3,
    }


@route(module='测试名称-模块', name='测试名称-PUT_PARAM')
def put(request: str, param1, from_=None, param3=5):
    # request 会是请求参数，参数列表中没有 HttpRequest
    return {
        'request': request,
        'param1': param1,
        'from': from_,
        'param3': param3,
    }


@route(module='测试名称-模块', name='测试名称-DELETE_PARAM')
def delete(request, param1, from_=None, param3=5, **kwargs):
    # 未在函数的参数列表中声明的请求参数，会出现在 kwargs 中
    return {
        'param1': param1,
        'from': from_,
        'param3': param3,
        'variable_args': kwargs
    }
