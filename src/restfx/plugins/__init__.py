from abc import ABC, abstractmethod


class PluginBase(ABC):
    def __init__(self):
        self.app = None

    def init_app(self, app):
        self.app = app

    @abstractmethod
    def requesting(self, request):
        pass

    @abstractmethod
    def requested(self, request, response):
        pass

    def dispose(self):
        pass
