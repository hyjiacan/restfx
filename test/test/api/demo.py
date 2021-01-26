from restfx import route
from restfx.http import HttpRequest
from restfx.http import FileStorage


@route(module='测试名称-模块', name='测试名称-GET', extname='jsp', auth=False)
def get(request, param1, param3: int = 5):
    """

    :param request:第1个参数 内置类型 <i>HttpRequest</i>
    :param param1:第2个参数 <span style="color:red">必填</span>
    :param param2:第3个参数
    :param param3:第4个参数
    :return: 返回值为参数字典
    """
    # request 会是 HttpRequest
    return {
        'param1': param1,
        # 'param2': param2,
        'param3': param3,
    }


@route(module='测试名称-模块', name='测试名称-POST_PARAM')
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
def put(request: str, param1: FileStorage):
    """

    :param request:第1个参数
    :param param1:需要上传一个文件
    :return: 返回值为参数字典
    """
    # request 会是请求参数，参数列表中没有 HttpRequest
    return {
        'request': request,
        'param1': {
            'filename': param1.filename,
            'type': param1.mimetype
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
