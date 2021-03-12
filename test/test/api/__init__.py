from restfx import route


@route('声明在包中的模块', '包路由', auth=False, extname='asp')
def get():
    """
    描述：这是一个<b>包路由</b>
    :return:
    """
    return {
        'data': '来自包中的数据'
    }
