# -*- coding: utf-8 -*-
import os

# 唯一的 APP_ID，用于在多进程时共享 session 数据
# 可以随意更改
APP_ID = '{APP_ID}'

# 是否处于调试模式
DEBUG = True

# 项目根目录
ROOT = os.path.dirname(__file__)

# 调试服务器 IP
HOST = '127.0.0.1'

# 调试服务器端口
PORT = 9127

# API接口前缀
API_PREFIX = 'api'

# 静态资源映射
STATIC_MAP = {
    # 尝试访问: http://127.0.0.1:9127/static/index.html
    '/static': os.path.join(ROOT, 'static')
}

# 路由映射
ROUTES_MAP = {
    'foo': 'bar'
}

# 是否启用严格模式
STRICT_MODE = False
