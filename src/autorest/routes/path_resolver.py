import inspect
import os

from ..base.app_context import AppContext
from ..base.request import HttpRequest
from ..base.response import HttpResponseNotFound, HttpResponseServerError, HttpResponse
from ..util.utils import load_module, get_func_args, get_func_info


class PathResolver:
    def __init__(self, context: AppContext,
                 modules_cache: dict,
                 entry_cache: dict,
                 request: HttpRequest,
                 method: str,
                 entry: str,
                 name: str):
        self.context = context
        self.modules_cache = modules_cache
        self.entry_cache = entry_cache
        self.request = request
        self.entry = entry
        method = method.lower()
        self.method = method

        # 如果指定了名称，那么就加上
        # 如：name = 'detail'
        #   func_name = get_detail
        if name:
            func_name = '%s_%s' % (method, name.lower())
        else:
            func_name = method
        self.func_name = func_name

        # 处理映射
        # 对应的模块(文件路径）
        self.module_name = self.get_route_map(entry)

        self.fullname = ''

    def check(self):
        module_name = self.module_name

        if module_name is None:
            self.context.logger.warning('Cannot find route map in RESTFUL_DJ.routes: %s' % self.entry)
            return HttpResponseNotFound()

        # 如果 module_name 是目录，那么就查找 __init__.py 是否存在
        abs_path = os.path.join(self.context.ROOT, module_name.replace('.', os.path.sep))
        if os.path.isdir(abs_path):
            self.context.logger.info('Entry "%s" is package, auto load module "__init__.py"' % module_name)
            module_name = '%s.%s' % (module_name, '__init__')
        elif not os.path.exists('%s.py' % abs_path):
            return HttpResponseNotFound()

        self.module_name = module_name

        # 完全限定名称
        self.fullname = '%s.%s' % (module_name, self.func_name)

    def resolve(self):
        try:
            func_define = self.get_func_define()
        except Exception as e:
            message = 'Load entry "%s" failed' % self.module_name
            self.context.logger.error(message, e)
            return HttpResponseNotFound()

        # 如果 func_define 为 False ，那就表示此函数不存在
        if func_define is False:
            message = 'Route "%s.%s" not found' % (self.module_name, self.func_name)
            self.context.logger.info(message)
            return HttpResponseNotFound()

        if func_define is HttpResponse:
            return func_define

        return self.invoke_handler(self.request, func_define['func'], func_define['args'])

    def get_route_map(self, route_path):
        # 命中
        hit_route = None
        for root_path in self.context.routes_map:
            if route_path.startswith(root_path):
                hit_route = root_path, self.context.routes_map[root_path]
                break

        if hit_route is None:
            return None

        # 将请求路径替换为指定的映射路径
        return ('%s%s' % (hit_route[1], route_path[len(hit_route[0]):])).strip('.')

    def get_func_define(self):
        fullname = self.fullname
        func_name = self.func_name
        module_name = self.module_name

        # 缓存中有这个函数
        if fullname in self.entry_cache.keys():
            return self.entry_cache[fullname]

        # 缓存中没有这个函数，去模块中查找
        # ---------------

        try:
            # 如果不加上fromlist=True,只会导入目录
            # noinspection PyTypeChecker
            # __import__ 自带缓存
            entry_define = load_module(module_name)
        except Exception as e:
            message = 'Load module "%s" failed' % module_name
            self.context.logger.error(message, e)
            return HttpResponseNotFound()

        # 模块中也没有这个函数
        if not hasattr(entry_define, func_name):
            # 函数不存在，更新缓存
            self.entry_cache[func_name] = False
            return False

        # 模块中有这个函数
        # 通过反射从模块加载函数
        func = getattr(entry_define, func_name)
        if not self.is_valid_route(func):
            msg = '%s\n\tDecorator "@route" not found on function "%s", did you forgot it ?' % (
                get_func_info(func),
                fullname
            )
            self.context.logger.warning(msg)
            # 没有配置装饰器@route，则认为函数不可访问，更新缓存
            self.entry_cache[func_name] = False
            return False

        self.entry_cache[fullname] = {
            'func': func,
            # 该函数的参数列表
            # 'name': {
            #     'annotation': '类型', 当未指定类型时，无此项
            #     'default': '默认值'，当未指定默认值时，无此项
            # }
            'args': get_func_args(func, self.context.logger)
        }

        return self.entry_cache[fullname]

    def invoke_handler(self, request, func, args):
        try:
            return func(request, args)
        except Exception as e:
            message = '\t%s' % get_func_info(func)
            self.context.logger.error(message, e)
            return HttpResponseServerError('%s: %s' % (message, str(e)))

    @staticmethod
    def is_valid_route(func):
        source = inspect.getsource(func)
        lines = source.split('\n')
        for line in lines:
            if line.startswith('def '):
                # 已经查找到了函数定义部分了，说明没有找到
                return False

            if line.startswith('@route('):
                # 是 @route 装饰器行
                return True
        return False
