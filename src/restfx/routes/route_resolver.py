import os
from typing import Dict, Optional

from ..config import AppConfig
from ..http.response import HttpNotFound, HttpResponse
from ..util import utils
from ..util.func_util import FunctionDescription


class RouteResolver:
    def __init__(self, config: AppConfig,
                 entry_cache: Dict[str, Optional[FunctionDescription]],
                 method: str,
                 entry: str):
        self.config = config
        self.entry_cache = entry_cache
        self.entry = entry
        self.method = method.lower()
        from ..util import Logger
        self.logger = Logger.get(config.app_id)

    def _get_module_abs_path(self, module_name):
        abs_path = os.path.join(self.config.ROOT, module_name)

        if os.path.isdir(abs_path):
            # 如果 module_name 是目录，那么就查找 __init__.py 是否存在
            self.logger.info('Entry "%s" is package, auto load module "__init__.py"' % module_name)
            return '%s%s%s' % (module_name, os.path.sep, '__init__')

        if os.path.exists('%s.py' % abs_path):
            return module_name

        return None

    def resolve(self) -> [FunctionDescription, HttpResponse]:
        # entry 可能包含扩展名
        temp = self.entry.split('.')
        entry = temp[0]
        if len(temp) > 1:
            extname = temp[1]
        else:
            extname = None
        # 处理映射
        # 对应的模块(包或模块路径，使用 . 分隔）
        module_name = self.get_route_map(entry)

        if module_name is None:
            self.logger.warning(
                'Cannot find route "%s" in routes_map' % self.entry)
            return HttpNotFound()

        func_name = self.method
        module_path = module_name.replace('.', os.path.sep)
        # 先检查完整路径是否存在
        module_abs_path = self._get_module_abs_path(module_path)
        if module_abs_path is None:
            # 再检查 append 函数是否存在
            # 将请求路径拆分成 entry 和 name
            temp = module_path.split(os.path.sep)
            name = temp.pop()
            module_path = os.path.sep.join(temp)
            module_abs_path = self._get_module_abs_path(module_path)

            if module_abs_path is None:
                return HttpNotFound()

            module_name = module_abs_path.replace(os.path.sep, '.')

            # 如果指定了名称，那么就加上
            # 如：name = 'detail'
            #   func_name = get_detail
            func_name = '%s_%s' % (self.method, name.lower())

        # 完全限定名称
        fullname = '%s.%s' % (module_name, func_name)
        try:
            desc = self._get_handler_info(module_name, func_name, fullname)
        except Exception as e:
            message = 'Failed to load entry "%s": %s' % (self.entry, fullname)
            self.logger.error(message, e)
            return HttpNotFound()

        # 检查 extname 是否一致
        if isinstance(desc, FunctionDescription) and desc.decorator['extname'] != extname:
            message = 'Failed to load entry "%s": extname "%s" is not exactly match with "%s"' % (
                self.entry, extname, desc.decorator['extname'])
            self.logger.warning(message)
            return HttpNotFound()

        return desc

    def get_route_map(self, route_path):
        # 命中
        hit_route = None
        for root_path in self.config.routes_map:
            if route_path.startswith(root_path):
                hit_route = root_path, self.config.routes_map[root_path]
                break

        if hit_route is None:
            return None

        # 将请求路径替换为指定的映射路径
        return ('%s%s' % (hit_route[1], route_path[len(hit_route[0]):])).replace('/', '.').strip('.')

    def _get_handler_info(self, module_name, func_name, fullname) -> [FunctionDescription, HttpResponse]:
        # 缓存中有这个函数
        if fullname in self.entry_cache.keys():
            return self.entry_cache[fullname]

        # 缓存中没有这个函数，去模块中查找
        # ---------------

        try:
            entry_define = utils.load_module(module_name.replace('/', '.'))
        except Exception as e:
            message = 'Failed to load module "%s"' % module_name
            self.logger.error(message, e)
            return HttpNotFound()

        # 模块中也没有这个函数
        if not hasattr(entry_define, func_name):
            # 函数不存在，更新缓存
            self.entry_cache[func_name] = None
            return HttpNotFound()

        # 模块中有这个函数
        # 通过反射从模块加载函数
        func = getattr(entry_define, func_name)
        import inspect
        from . import Collector
        filename = inspect.getmodule(func).__file__
        decorator = Collector.get(self.config.app_id).resolve_routes(filename, func_name)

        if decorator is None:
            msg = '%s\n\tDecorator "@route" not found on function "%s", did you forgot it ?' % (
                utils.get_func_info(func),
                fullname
            )
            self.logger.warning(msg)
            # 没有配置装饰器@route，则认为函数不可访问，更新缓存
            self.entry_cache[func_name] = None
            return HttpNotFound()

        func_desc = FunctionDescription(func)
        func_desc.decorator = decorator
        self.entry_cache[fullname] = func_desc

        return self.entry_cache[fullname]
