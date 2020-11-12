import os

from src.autorest import App, FileSessionProvider

if __name__ == '__main__':
    root = os.path.dirname(__file__)
    app = App(root, debug_mode=True, session_provider=FileSessionProvider, session_extra_params={
        'path': 'G:/sessions'
    })
    app.map_routes({
        'x': 'test'
    })
    app.startup()
