# restfx

Python3 的 restful 多应用自动路由框架。

> 底层基于 [werkzeug](https://werkzeug.palletsprojects.com/)

## 为什么要使用此框架

开发此框架的目标是 **提升开发效率**。

我也曾使用过 **Django**，**Flask**。
但其繁琐的路由注册，以及参数声明，让人难以接受，简单的功能，却要写一大段代码。

此框架的前身是 [restful-dj](https://gitee.com/hyjiacan/restful-dj)，
这是一个为 Django 开发的框架。

在使用中慢慢发现，在 restful 接口上，Django 给了我太多我用不到的东西，
臃肿不堪，于是才决定基于 `werkzeug` 开发。

此框架解决了以下问题：

- 没有繁锁的路由配置，免去路由注册。仅仅需要对模块根进行注册，模块下的所有路由都会自动被收集调用
- 不需要对路由 url 进行显示配置，完全自动解析 
- 自动解析/校验请求参数，并填充到路由函数，省去繁锁的参数获取/类型校验。需要做的仅仅是编写一个函数，并添加函数参数的类型声明 
- 提供 **接口列表页面** 以及接口测试支持，让接口随码更新，不用手动维护API文档。 见[截图](#截图)
- 提供 [路由注入][2] 支持，以通过参数方式向路由指定请求参数外的数据/函数，从而避免一些频繁的 `import` 和重复代码

**此框架的弊端: 不支持将参数作为 url 路径的一部分**

## 安装

```shell script
pip install restfx
```

`Since 0.7.1` 安装后，可以通过 CLI 工具 `restfx` 命令创建基本项目结构:

```shell script
restfx create projectname
```

> 使用此命令，可能需要将 `restfx` 安装到全局环境中。

## 文档

使用文档见 [Gitee Wiki][1]

## 创建应用

```python
import os

import restfx

if __name__ == '__main__':
    root = os.path.dirname(__file__)
    app = restfx.App(root, api_prefix='any/prefix', debug=True)
    app.map_routes({
        'x': 'test'
    })
    app.map_static(static_map={})
    app.startup(host='127.0.0.1', port=9127)
```

### 编写路由

*test/api/demo.py*

```python
from restfx import route
from restfx.http import HttpRequest, HttpFile


@route(module='测试名称-模块', name='测试名称-GET')
def get(request, param1, param2=None, param3: int = 5):
    # request 会是 HttpRequest
    return {
        'param1': param1,
        'param2': param2,
        'param3': param3,
    }


@route(module='测试名称-模块', name='测试名称-POST_PARAM')
def get_param(param1, req: HttpRequest, from_=None, param3=5):
    # req 会是 HttpRequest
    return {
        'param1': param1,
        'from': from_,
        'param3': param3,
    }


@route(module='测试名称-模块', name='测试名称-PUT_PARAM')
def put(request: str, param1, file: HttpFile, param3=5):
    # request 会是请求参数，参数列表中没有 HttpRequest
    return {
        'request': request,
        'param1': param1,
        'param3': param3,
    }


@route(module='测试名称-模块', name='测试名称-DELETE_PARAM')
def delete(request, param1, from_=None, param3=5, **kwargs):
    # 未在函数的参数列表中声明的请求参数，会出现在 kwargs 中
    return {
        'param1': param1,
        'from': from_,
        'param3': param3,
        'variable_args': kwargs
    }

```

## 截图

以下截图为接口列表，对应的路由声明源码见

- [test/test/api/__init__.py][11]
- [test/test/api/demo.py][12]


以下截图仅在 [Gitee仓库目录][3] 可见

![list](assets/1.png)

![test](assets/2.png)


[1]: https://gitee.com/hyjiacan/restfx/wikis
[2]: https://gitee.com/hyjiacan/restfx/wikis/0B.%20%E8%B7%AF%E7%94%B1%E6%B3%A8%E5%85%A5?sort_id=3519061
[3]: https://gitee.com/hyjiacan/restfx#%E6%88%AA%E5%9B%BE
[11]: https://gitee.com/hyjiacan/restfx/blob/master/test/test/api/__init__.py
[12]: https://gitee.com/hyjiacan/restfx/blob/master/test/test/api/demo.py

## TODOLIST

- [ ] 添加 自定义接口页面JS资源加载，以支持对请求和响应的数据进行额外处理
  - 类似于勾子函数
