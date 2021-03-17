from restfx import route
from ..tools import b64


@route('声明在包中的模块', '包路由', auth=False, extname='asp')
def get(content, session):
    """
    这是一个<b>包路由</b>
    :return:
    """
    old = None
    if session:
        old = session.get('old')
        session.set('old', content)
    return {
        'data': '来自包中的数据',
        'content': content,
        'old': old
    }


@route('包中的模块2', '对请求的数据base64编码后返回', auth=False)
def post_base64(data: str):
    return b64.enc_str(data)
