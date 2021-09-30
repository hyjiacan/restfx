import os

from . import __meta__
from .app import App
from .routes.decorator import route
from .routes.parameter_interface import IParam
from .routes.validator import Validator

__version__ = __meta__.version

val = Validator
"""
Validator 的简短别名
"""

env = os.environ.get('RESTFX_ENV')
"""
指定执行环境环境，通常情况下，可选值为 dev 或者 prod 默认为 None
"""

# 如果没有指定，默认使用 prod
if env:
    env = env.lower()
else:
    env = None

__all__ = [
    'App',
    'route',
    'val',
    'IParam',
    'env',
    '__version__'
]
