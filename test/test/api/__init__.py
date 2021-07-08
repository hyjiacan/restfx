from restfx import route
from ..tools import b64
from ..tools.enums import OpTypes
from ..tools.validators import MyValidator


def get_old_value():
    from restfx.globs import session, req_store
    return session.get('old'), req_store.get('a')


@route('', '包路由', auth=False, extname='asp', validators=(
        MyValidator('content').range(10, 120).all_a(),
))
def get(request, content, session, a, e: OpTypes, **kwargs):
    """
    这是一个<b>包路由</b>

    注释可以写好几行

    这是第三行

    这是第4行

    这是第伍行

        这是第六行 (这行前面有空白字符)
    :param content: 这是请求时携带的内容参数

    这里面也可以写代码：
        var a = 5;
        ajax.get('/api/test.asp', {content: 5})
    但是在导出的文件中，参数中的代码块不能换行。
    :return: 返回值没有什么特殊的

    但是我想在此添加一个代码块

        def func(a: int, b: bool):
            val_a = a
            val_b = b

            return {
                'a': a,
                'b': b
            }


        def func2():
            pass

    遇到缩进消失，或者连续两个空行时，表示代码段结束，这与 markdown 语法是一样的
    """
    old = None
    if session:
        # 当需要指定参数时，使用 request.context(a=2)
        # 或者使用
        with request.context(a=2):
            old = get_old_value()
        session.set('old', content)
    return {
        'data': '来自包中的数据',
        'content': content,
        'old': old,
        'enum': e.name,
        'a': a,
        'b[]': kwargs.get('b')
    }


@route('包中的模块2', '对请求的数据base64编码后返回', auth=False)
def post_base64(request, data: str):
    """

    :param data: 参数的描述

    也是可以换行的

    还可以包含代码段 `a=123`
    :return:返回的是

    `base64` 编码的数据
    """
    from io import BytesIO
    buffer = BytesIO(b64.enc_str(data).encode())
    from restfx.http import FileResponse
    return FileResponse(buffer, attachment='测试文件名.txt', request=request, content_type='text/plain')
