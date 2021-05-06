from abc import ABC, abstractmethod


class IParam(ABC):
    """
    自定义参数类型时，通过实现此接口以进行参数类型的转换
    """

    @classmethod
    @abstractmethod
    def parse(cls, value: (list, dict)):
        raise NotImplemented()
