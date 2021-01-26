# -*- coding=utf8 -*-

# IMPORT ROUTES BEGIN
from test.api.demo import get as test_api_demo_get
from test.api.demo import get_param as test_api_demo_get_param
from test.api.demo import put as test_api_demo_put
from test.api.demo import delete as test_api_demo_delete
from test.api.__init__ import get as test_api_____init_____get
# IMPORT ROUTES END


# LIST ROUTES BEGIN
routes = [
    # 测试名称-模块-测试名称-GET
    ['GET', '/test/demo.jsp', test_api_demo_get],
    # 测试名称-模块-测试名称-POST_PARAM
    ['GET', '/test/demo/param', test_api_demo_get_param],
    # 测试名称-模块-测试名称-PUT_PARAM
    ['PUT', '/test/demo', test_api_demo_put],
    # 测试名称-模块-测试名称-DELETE_PARAM
    ['DELETE', '/test/demo', test_api_demo_delete],
    # 声明在包中的模块-包路由
    ['GET', '/test.asp', test_api_____init_____get]
]
# LIST ROUTES END
