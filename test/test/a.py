from src.autorest import route


@route('测试', 'get')
def get(request):
    return 'test.a'
