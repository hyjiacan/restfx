import os

from src.autorest import App

if __name__ == '__main__':
    root = os.path.dirname(__file__)
    app = App(root, debug_mode=True)
    app.map_routes({
        'x': 'test'
    })
    app.startup()
