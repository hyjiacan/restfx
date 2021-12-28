from abc import ABC, abstractmethod


class PluginBase(ABC):
    """
    插件基类
    """

    def __init__(self, name: str = None, version: str = None, description: str = None):
        """

        :param name: 指定插件名称
        :param version: 指定插件版本
        :param description: 指定插件描述
        """
        self.name = name
        self.version = version
        self.description = description

    @abstractmethod
    def setup(self, app):
        """
        初始化插件
        :param app:
        :return:
        """
        raise NotImplemented()

    @abstractmethod
    def destroy(self):
        """
        销毁插件
        :return:
        """
        raise NotImplemented()
