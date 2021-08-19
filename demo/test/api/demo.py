from test.tools.enums import OpTypes

from restfx import val
from restfx import route
from restfx.http import HttpFile
from restfx.http import HttpRequest


@route(module='测试名称-模块', name='测试名称-GET', extname='jsp', auth=False, op_type=OpTypes.Query, validators=(
        val('param1').range(2, 2)
))
def get(request, _injection, param1=(1, 2), param2={}):
    """

    :param request: HttpRequest
    :param _injection:
    :param param1:第1个参数
    :param param2:第2个参数
    :return: 返回值为参数字典
    """
    # request 会是 HttpRequest

    temp = []
    for i in range(20):
        temp.append({
            'i': i,
            'p': i ^ i,
            'o': i & i
        })

    data = {
        'injection': _injection,
        'param1': param1,
        'param2': param2,
        'temp': temp
    }
    return data


@route(module='测试名称-模块', name='测试名称-GET_APPEND_PARAM')
def get_param(param1, req: HttpRequest, from_=None, param3=5):
    """

    :param param1:第1个参数
    :param req:第2个参数
    :param from_:第3个参数
    :param param3:第4个参数
    :return: 返回值为参数字典
    """
    # req 会是 HttpRequest
    return {
        'param1': param1,
        'from': from_,
        'param3': param3,
    }


@route(module='测试名称-模块', name='测试名称-PUT_PARAM', auth=False)
def put(request: int, file: HttpFile):
    """

    :param request:第1个参数
    :param file:需要上传一个文件
    :return: 返回值为参数字典
    """
    # request 会是请求参数，参数列表中没有 HttpRequest
    return {
        'request': request,
        'param1': {
            'filename': file.stream.filename if file else None,
            'type': file.mimetype
        }
    }


@route(module='测试名称-模块', name='测试名称-DELETE_PARAM')
def delete(request, param1, from_=None, param3=5, **kwargs):
    """

    :param request:第1个参数
    :param param1:第2个参数
    :param from_:第3个参数
    :param param3:第4个参数
    :return: 返回值为参数字典
    """
    # 未在函数的参数列表中声明的请求参数，会出现在 kwargs 中
    return {
        'param1': param1,
        'from': from_,
        'param3': param3,
        'variable_args': kwargs
    }
