from restfx import route
from ..tools import b64


def get_old_value():
    from restfx.globals import session, req_store
    return session.get('old'), req_store.get('a')


@route('', '包路由', auth=False, extname='asp')
def get(request, content, session):
    """
    这是一个<b>包路由</b>

    注释可以写好几行

    这是第三行

    这是第4行

    这是第伍行

        这是第六行 (这行前面有空白字符)
    :return:
    """
    old = None
    if session:
        # 当需要指定参数时，使用 request.context(a=2)
        # 或者使用
        # from restfx.globals import req_store
        # req_store.setdefault('a', 2)
        with request.context(a=2):
            old = get_old_value()
        session.set('old', content)
    return {
        'data': '来自包中的数据',
        'content': content,
        'old': old
    }


@route('包中的模块2', '对请求的数据base64编码后返回', auth=False)
def post_base64(data: str):
    """

    :param data: 参数的描述

    也是可以换行的

    还可以包含代码段 `a=123`
    :return:返回的是

    `base64` 编码的数据
    """
    return b64.enc_str(data)
