# coding: utf-8

# 此模块用于收集路由

import os
import re
from os import path

# 生成：注册路由的代码 -- 模板
# 注意生成的代码中的缩进，使用的是空格
_REGISTER_STMT = "    # {module}-{name}\n    ['{method}', '{path}', {handler}]"
_CODE_TPL = """# -*- coding={encoding} -*-

   # IMPORT ROUTES BEGIN
   {imports}
   # IMPORT ROUTES END


   # REGISTER ROUTES BEGIN
   routes = [
   {routes}
   ]
   # REGISTER ROUTES END
   """


def _fake_route(module=None, name=None, **kwargs):
    """
    此函数用于帮助读取装饰器的参数
    :param module:
    :param name:
    :param kwargs:
    :return:
    """

    return {
        'module': module,
        'name': name,
        'kwargs': kwargs
    }


class Collector:
    def __init__(self, project_root: str, url_endswith_slash: bool):
        self.project_root = project_root
        self.url_endswith_slash = url_endswith_slash
        # 全局类列表
        self.global_classes = []

    def _get_env(self, *args):
        env = {}

        # 加载全局配置
        for arg in self.global_classes:
            env[arg.__name__] = arg

        # 加载接口参数
        # 若存在相同的名称，则会被覆盖
        for arg in args:
            env[arg.__name__] = arg
        return env

    def collect(self, routes_map: dict, *environments):
        """
        执行收集操作
        :return: 所有路由的集合
        """
        # 为 route 提供的执行环境
        # 读取在 settings.py 中配置的环境
        route_env = self._get_env(_fake_route, *environments)

        # 所有路由的集合
        routes = []

        if not routes_map:
            raise Exception(
                'Routes map is empty, did you forgot to call "restfx.map_routes(routes_map: dict)"')

        for (http_prefix, pkg_prefix) in routes_map.items():
            route_root = path.abspath(path.join(self.project_root, pkg_prefix.replace('.', path.sep)))

            # 遍历目录，找出所有的 .py 文件
            for (dir_name, dirs, files) in os.walk(route_root):
                for file in files:
                    # 不是 .py 文件，忽略
                    if not file.endswith('.py'):
                        continue

                    fullname = path.abspath(path.join(dir_name, file))
                    # 解析文件
                    self.get_route_defines(route_root, fullname, http_prefix, pkg_prefix, routes, route_env)

                for sub_dir_name in dirs:
                    pkg_file = path.abspath(path.join(sub_dir_name, '__init__.py'))
                    if path.exists(pkg_file) and path.isfile(pkg_file):
                        self.get_route_defines(route_root, pkg_file, http_prefix, pkg_prefix, routes, route_env)

        return routes

    def get_route_defines(self, route_root, fullname, http_prefix, pkg_prefix, routes, route_env):
        for define in self.resolve_file(route_root, fullname, http_prefix, pkg_prefix, route_env):
            # 返回 None 表示没有找到定义
            if define is None:
                continue
            routes.append(define)

    def resolve_file(self, route_define, fullname, http_prefix, pkg_prefix, route_env: dict):
        """
        解析文件
        :param route_env:
        :param pkg_prefix:
        :param http_prefix: http 请求前缀
        :param route_define: 路由文件的根路径
        :param fullname: 文件的完整路径
        :return: 没有路由时返回 None
        """
        with open(fullname, encoding='utf-8') as python_fp:
            lines = python_fp.readlines()
            python_fp.close()
        source = ''.join(lines)

        # 解析路由的定义
        # defines = re.compile(r'^@(route\(.+?\)).*(\n.*?)+^def (.+?)\(', re.M).findall(source)
        defines = re.compile(r'^@(route\(.+?\))(.*?)^def (.+?)\(', re.M | re.S).findall(source)
        # 没有找到定义，返回 None
        if len(defines) == 0:
            yield None

        # router_str 是在函数上声明的装饰器定义
        # other_lines 是装饰器与函数声明间的其它代码
        # func 是函数的名称
        for (router_str, other_lines, func) in defines:
            # 解析出请求的方法(method)与请求的指定函数名称
            method, name = self.resolve_func(func)
            # 利用 eval 解析出路由的定义（在这个文件中定义了与装饰器相同的函数，以便于读取装饰器的参数）
            router_str = router_str.replace('route', '_fake_route')
            define = eval(router_str, route_env)

            # 构造http请求的地址
            # -3 是为了干掉最后的 .py 字样
            pkg = re.sub(r'[/\\]', '', path.relpath(fullname, route_define))[0:-3]

            # 当是包时，移除 __init__ 部分
            if path.basename(fullname) == '__init__.py':
                http_path = '%s.%s' % (http_prefix, pkg[0:-len('__init__')])
            else:
                http_path = '%s.%s' % (http_prefix, pkg)

            # 当 map_routes 指定的 http_prefix 为空时，前导的 . 符号是多余的
            # 当路由文件为根目录下的 __init__.py 时，没有可访问的文件名
            # 此时会出现得到的路由为  xxx. 的情况
            # 所以在此移除末尾的 . 符号
            http_path = '/' + http_path.strip('.')

            # 如果指定了名称，就追加到地址后
            if name is not None:
                http_path += '/' + name

            if self.url_endswith_slash:
                http_path += '/'

            pkg = '%s.%s' % (pkg_prefix, pkg)
            # 唯一标识
            define['id'] = '%s_%s' % (pkg.replace('_', '__').replace('.', '_'), func)
            # 路由所在包名称
            define['pkg'] = pkg
            # 路由所在文件的完整路径
            define['file'] = fullname
            # 路由请求的处理函数
            define['handler'] = func
            # 路由的请求方法
            define['method'] = method
            # 路由的请求路径
            define['path'] = http_path

            yield define

    @staticmethod
    def resolve_func(func: str):
        """
        从处理函数中解析出路由的 method 与指定名称
        :param func:
        :return:
        """
        method, lodash, name = re.match(r'([a-z]+)(_(.+))?', func).groups()
        return method, name

    def persist(self, routes_map: dict, filename: str = '', encoding='utf8', *environments):
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

        print('Generating restful map file with encoding %s' % encoding)
        for route in self.collect(routes_map, *environments):
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

        print('Generate restful map file complete')
        if not filename:
            return content

        print('Persisting into file %s' % filename)
        with open(filename, mode='wt', encoding=encoding) as fp:
            fp.write(content)
            fp.close()
        print('Routes persisted')
