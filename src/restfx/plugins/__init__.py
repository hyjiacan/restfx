from abc import ABC


class PluginBase(ABC):
    def __init__(self):
        self.app = None

    def init_app(self, app):
        self.app = app

    def requesting(self, request):
        pass

    def requested(self, request, response):
        pass

    def dispose(self):
        pass
