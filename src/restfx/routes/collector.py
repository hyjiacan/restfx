# coding: utf-8

import ast
# 此模块用于收集路由
import os
import re
from os import path

from ..util import utils
from ..util.func_util import FunctionDescription

# 生成：注册路由的代码 -- 模板
# 注意生成的代码中的缩进，使用的是空格

_REGISTER_STMT = "    # {module}-{name}\n    ['{method}', '{path}', {handler}]"
_CODE_TPL = """# -*- coding={encoding} -*-

# IMPORT ROUTES BEGIN
{imports}
# IMPORT ROUTES END


# LIST ROUTES BEGIN
routes = [
{routes}
]
# LIST ROUTES END
"""


class Collector:
    def __init__(self, project_root: str, append_slash: bool):
        self.project_root = project_root
        self.append_slash = append_slash

    def collect(self, routes_map: dict):
        """
        执行收集操作
        :return: 所有路由的集合
        """
        # 所有路由的集合
        routes = []

        if not routes_map:
            raise Exception(
                'Routes map is empty, did you forgot to call "restfx.map_routes(routes_map: dict)"')

        for (http_prefix, pkg_prefix) in routes_map.items():
            route_root = path.abspath(path.join(self.project_root, pkg_prefix.replace('.', path.sep)))

            # 遍历目录，找出所有的 .py 文件
            for (dir_name, dirs, files) in os.walk(route_root):
                if dir_name == '__pycache__':
                    continue
                for file in files:
                    # 不是 .py 文件，忽略
                    if not file.endswith('.py'):
                        continue

                    # 可能是 __init__.py
                    fullname = path.abspath(path.join(dir_name, file))

                    # 解析文件
                    self.get_route_defines(route_root, fullname, http_prefix, pkg_prefix, routes)

        return routes

    def get_route_defines(self, route_root, fullname, http_prefix, pkg_prefix, routes):
        for define in self.resolve_file(route_root, fullname, http_prefix, pkg_prefix):
            # 返回 None 表示没有找到定义
            if define is None:
                continue
            routes.append(define)

    def resolve_file(self, route_define, fullname, http_prefix, pkg_prefix):
        """
        解析文件
        :param pkg_prefix:
        :param http_prefix: http 请求前缀
        :param route_define: 路由文件的根路径
        :param fullname: 文件的完整路径
        :return: 没有路由时返回 None
        """
        # 解析路由的定义
        envs, routes = self.resolve_routes(fullname)

        # 没有找到定义，返回 None
        if not routes:
            yield None

        # router_info 是在函数上声明的装饰器定义信息
        # func_name 是函数的名称
        for (func_name, router_info) in routes:
            # 解析出请求的方法(method)与请求的指定函数名称
            method, _, name = re.match(r'([a-z]+)(_(.+))?', func_name).groups()

            # 构造http请求的地址(将 路径分隔符号 \/ 替换成 . 符号)
            # -3 是为了干掉最后的 .py 字样
            pkg = re.sub(r'[/\\]', '.', path.relpath(fullname, route_define))[0:-3]

            is_package = path.basename(fullname) == '__init__.py'

            # 当是包时，移除 __init__ 部分
            if is_package:
                http_path = '%s.%s' % (http_prefix, pkg[0:-len('__init__')])
            else:
                http_path = '%s.%s' % (http_prefix, pkg)

            # 当 map_routes 指定的 http_prefix 为空时，前导的 . 符号是多余的
            # 当路由文件为根目录下的 __init__.py 时，没有可访问的文件名
            # 此时会出现得到的路由为  xxx. 的情况
            # 所以在此移除末尾FunctionDescription的 . 符号
            http_path = '/' + http_path.strip('.').replace('.', '/')

            # 如果指定了名称，就追加到地址后
            ext_mode = name is not None
            if ext_mode:
                http_path += '/' + name

            # 指定的 url 扩展名
            extname = router_info['extname']
            if extname is not None:
                http_path += '.' + extname

            if self.append_slash:
                http_path += '/'

            # 当是包时，移除 .__init__ 部分
            if is_package:
                pkg = '%s.%s' % (pkg_prefix, pkg[0:-len('__init__')])
            else:
                pkg = '%s.%s' % (pkg_prefix, pkg)

            pkg = pkg.rstrip('.')

            module = utils.load_module(pkg)
            handler_obj = getattr(module, func_name)
            handler_info = FunctionDescription(handler_obj)

            # 唯一标识
            router_info['id'] = '%s_%s' % (pkg.replace('_', '__').replace('.', '_'), func_name)
            # 路由所在包名称
            router_info['pkg'] = pkg
            # 路由所在文件的完整路径
            router_info['file'] = fullname
            # 路由请求的处理函数
            router_info['handler'] = func_name
            # 路由的请求方法
            router_info['method'] = method
            # 路由的请求路径
            router_info['path'] = http_path
            # 路由函数的描述
            router_info['handler_info'] = handler_info
            # 是否是包
            router_info['is_package'] = is_package
            # 是否是扩展模式
            router_info['ext_mode'] = ext_mode
            # 自定义的装饰器参数
            router_info['kwargs'] = router_info['kwargs']

            yield router_info

    def persist(self, routes_map: dict, filename: str = '', encoding='utf8'):
        """
        将路由持久化
        :param routes_map:
        :param filename:
        :param encoding:
        :return: 持久化的 python 代码
        :rtype: str or None
        """
        imports = []
        routes = []

        print('Generating routes map...')
        for route in self.collect(routes_map):
            # imports.append('from %s import %s as %s' % (route['pkg'], route['handler'], route['id']))
            imports.append('from %s import %s as %s' % (route['pkg'], route['handler'], route['id']))
            routes.append(_REGISTER_STMT.format(
                module=route['module'],
                name=route['name'],
                method=route['method'].upper(),
                path=route['path'],
                handler=route['id']
            ))

        content = _CODE_TPL.format(encoding=encoding, imports='\n'.join(imports), routes=',\n'.join(routes))

        print('Routes map data generated')
        if not filename:
            return content

        print('Persisting into file %s file with encoding %s' % (filename, encoding))
        with open(filename, mode='wt', encoding=encoding) as fp:
            fp.write(content)
            fp.close()
        print('Routes persisted')

    @staticmethod
    def resolve_routes(filename: str, func_name: str = None):
        """

        :param filename:
        :param func_name: 解析指定的函数
        :return:
        """
        with open(filename, encoding='utf-8') as python_fp:
            lines = python_fp.readlines()
            python_fp.close()
        ast_body = ast.parse(source=''.join(lines), filename=filename).body

        envs = {}
        routes = []

        for item in ast_body:
            if isinstance(item, ast.ImportFrom):
                level = item.level if hasattr(item, 'level') else 0
                module = utils.load_module(item.module, level)
                for name_item in item.names:
                    env_name = name_item.asname or name_item.name
                    envs[env_name] = getattr(module, name_item.name)
                continue
            # if isinstance(item, ast.ClassDef):
            #     continue
            # if isinstance(item, ast.Assign):
            #     continue
            if not isinstance(item, ast.FunctionDef):
                continue

            if func_name is not None and item.name != func_name:
                continue

            # Find out the @route decorator
            decorator_info = Collector.get_route_decorator(item, envs)
            if decorator_info is None:
                continue

            if func_name is not None:
                return envs, decorator_info

            routes.append((item.name, decorator_info))

        return envs, routes if func_name is None else None

    @staticmethod
    def get_route_decorator(func_def: ast.FunctionDef, envs: dict = None):
        for decorator in func_def.decorator_list:
            if not decorator.func:
                continue
            if decorator.func.id != 'route':
                continue

            keywords = {}
            for keyword in decorator.keywords:
                arg_name = keyword.arg
                value = keyword.value
                if isinstance(value, ast.Attribute):
                    arg_value = getattr(envs[value.value.id], value.attr)
                else:
                    # 其它类型暂时不支持
                    # 统一使用原始值
                    arg_value = getattr(value, keyword.value._fields[0])

                keywords[arg_name] = arg_value

            route_module = None
            route_name = None
            route_extname = None

            # 在此不需要考虑其它的数据类型，因为声明的时候全是 字符串
            if len(decorator.args) == 1:
                route_module = decorator.args[0].s
            elif len(decorator.args) == 2:
                route_module = decorator.args[0].s
                route_name = decorator.args[1].s
            elif len(decorator.args) == 3:
                route_module = decorator.args[0].s
                route_name = decorator.args[1].s
                route_extname = decorator.args[2].s

            if route_module is None and 'module' in keywords:
                route_module = keywords['module']
                del keywords['module']
            if route_name is None and 'name' in keywords:
                route_name = keywords['name']
                del keywords['name']
            if route_extname is None and 'extname' in keywords:
                route_extname = keywords['extname']
                del keywords['extname']

            return {
                'module': route_module,
                'name': route_name,
                'extname': route_extname,
                'kwargs': keywords
            }
        return None
