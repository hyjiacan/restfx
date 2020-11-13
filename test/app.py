import os

from autorest import App
from test.session_provider import MysqlSessionProvider

if __name__ == '__main__':
    root = os.path.dirname(__file__)
    app = App(root, debug_mode=True, session_provider=MysqlSessionProvider(20))
    app.map_routes({
        'x': 'test'
    })
    app.startup()
