from restfx import route


@route('声明在包中的模块', '包路由', auth=False)
def get(**kwargs):
    """
    sdfs
    :param foo: adsad
    :return:
    """
    return {
        'data': kwargs
    }
