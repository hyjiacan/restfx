from .app import App
from .routes.decorator import route
from .routes.validator import Validator

# 设置一个简短的别名 for Validator
val = Validator

__all__ = [
    'App',
    'route',
    'val'
]
