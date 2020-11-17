import json
from collections import OrderedDict
from functools import wraps

from ..http import HttpRequest
from ..http import HttpResponse, HttpResponseBadRequest, JsonResponse
from ..routes.meta import RouteMeta
from ..middleware import MiddlewareManager
from ..util.func_util import ArgumentSpecification, get_func_info


def route(module=None, name=None, **kwargs):
    """
    用于控制路由的访问权限，路由均需要添加此装饰器，若未添加，则不可访问
    :param module: str 路由所属模块，一般在查询权限时会用到
    :param name: str 路由名称，一般在查询权限时会用到
    用法：
    @route('用户管理', '编辑用户')
    def get(req):
        pass
    """

    def invoke_route(func):
        @wraps(func)
        def caller(*args):
            # 参数长度不为 2 时，认为是用户调用
            if len(args) != 2:
                return func(*args)

            # Http 请求对象
            # :type HttpRequest
            request = args[0]
            # 函数声明时定义的参数列表
            # :type OrderedDict
            func_args = args[1]

            # 如果传入的参数第一个不是 request，第二个不是 OrderedDict，
            # 那么就认为是用户调用，而不是路由调用
            # 此时直接将原参数传给 func 进行调用
            if not isinstance(request, HttpRequest) or not isinstance(func_args, OrderedDict):
                return func(*args)

            meta = RouteMeta(
                func,
                func_args,
                route_id='%s_%s' % (func.__module__.replace('_', '__').replace('.', '_'), func.__name__),
                module=module,
                name=name,
                method=request.method,
                path=request.path,
                kwargs=kwargs,
            )

            return _invoke_with_route(request, meta)

        return caller

    return invoke_route


def _invoke_with_route(request: HttpRequest, meta: RouteMeta):
    mgr = MiddlewareManager(
        request,
        meta
    )

    func_args = meta.func_args
    func = meta.handler

    # 调用中间件，以处理请求
    result = mgr.begin()

    # 返回了 HttpResponse，直接返回此对象
    if isinstance(result, HttpResponse):
        return mgr.end(result)

    # 返回了 False，表示未授权访问
    if result is False:
        return mgr.end(HttpResponseUnauthorized())

    # 处理请求中的json参数
    # 处理后可能会在 request 上添加一个 json 的项，此项存放着json格式的 body 内容
    # noinspection PyTypeChecker
    _process_json_params(request)

    result = mgr.before_invoke()

    # 返回了 False，表示未授权访问
    if result is False:
        return mgr.end(HttpResponseUnauthorized())

    # 返回了 HttpResponse ， 直接返回此对象
    if isinstance(result, HttpResponse):
        return mgr.end(result)

    # 调用路由处理函数
    arg_len = len(func_args)
    if arg_len == 0:
        return mgr.end(_wrap_http_response(mgr, func()))

    # 有参数，自动从 queryString, POST 或 json 中获取
    # 匹配参数

    actual_args = _get_actual_args(request, func, func_args)

    if isinstance(actual_args, HttpResponse):
        return mgr.end(actual_args)

    result = func(**actual_args)

    return mgr.end(_wrap_http_response(mgr, result))


def _process_json_params(request):
    """
    参数处理
    :return:
    """
    if request.content_type != 'application/json':
        return

    # 如果请求是json类型，就先处理一下

    body = request.data

    if not body:
        return

    try:
        request.BODY = json.loads(body.decode())
    except Exception as e:
        request.context.logger.warning('Deserialize request body fail: %s' % str(e))


def _get_parameter_str(args: OrderedDict):
    return '\n\t\t'.join([str(args[arg]) for arg in args])


def _get_value(data: dict, name: str, arg_spec: ArgumentSpecification, backup: dict = None):
    """

    :param data:
    :param name:
    :param arg_spec:
    :return: True 表示使用默认值 False 表示未使用默认值 None 表示无值
    """
    if name in data:
        return False, data[name]

    alias = arg_spec.alias

    if alias is not None and alias in data:
        return False, data[alias]

    if isinstance(backup, dict):
        if name in backup:
            return False, backup[name]

        if alias is not None and alias in backup:
            return False, backup[alias]

    # 使用默认值
    if arg_spec.has_default:
        return True, arg_spec.default

    # 缺少无默认值的参数
    return None, None


def _get_actual_args(request: HttpRequest, func, args: OrderedDict) -> dict or HttpResponse:
    method = request.method.lower()
    actual_args = {}

    # 已使用的参数名称，用于后期填充可变参数时作排除用
    used_args = []
    # 是否声明了可变参数
    has_variable_args = False

    # noinspection PyUnresolvedReferences
    arg_source = request.GET if method in ['delete', 'get'] else request.POST

    for arg_name in args.keys():
        arg_spec = args.get(arg_name)

        # 如果是可变参数：如: **kwargs
        # 设置标记，以在后面进行填充
        if arg_spec.is_variable:
            has_variable_args = True
            continue

        # 以及情况将传入 HttpRequest 对象
        # 1. 当参数名称是 request 并且未指定类型
        # 2. 当参数类型是 HttpRequest 时 (不论参数名称，包括 request)
        # 但是，参数名称是 request 但其类型不是 HttpRequest ，就会被当作一般参数处理
        if arg_name == 'request' and not arg_spec.has_annotation:
            actual_args[arg_name] = request
            continue
        if arg_spec.annotation == HttpRequest:
            actual_args[arg_name] = request
            continue

        # noinspection PyUnresolvedReferences
        use_default, arg_value = _get_value(arg_source, arg_name, arg_spec, request.BODY)

        # 未找到参数
        if use_default is None:
            msg = '%s\n\tMissing required argument "%s":\n\t\t%s' % (
                get_func_info(func),
                arg_name,
                _get_parameter_str(args)
            )
            request.context.logger.warning(msg)
            return HttpResponseBadRequest(msg)

        # 使用默认值
        if use_default is True:
            actual_args[arg_name] = arg_value
            used_args.append(arg_name)
            continue

        # 未指定类型
        if not arg_spec.has_annotation:
            actual_args[arg_name] = arg_value
            used_args.append(arg_name)
            continue

        # 当值为 None 时，不作数据类型校验
        if arg_value is None:
            actual_args[arg_name] = arg_value
            used_args.append(arg_name)
            continue

        # 检查类型是否一致 #

        # 类型一致，直接使用
        if isinstance(arg_value, arg_spec.annotation):
            actual_args[arg_name] = arg_value
            used_args.append(arg_name)
            continue

        # 类型不一致，尝试转换类型

        # 当声明的参数类型是布尔类型时，收到的值可能是一个字符串（其值为 true 、 false）
        if arg_spec.annotation is bool and isinstance(arg_value, str):
            if arg_value == 'true':
                actual_args[arg_name] = True
                used_args.append(arg_name)
            elif arg_value == 'false':
                actual_args[arg_name] = False
                used_args.append(arg_name)
            else:
                request.context.logger.error(
                    'Value for "%s!%s" may be incorrect (a boolean value expected: true/false): %s' % (
                        func.__name__, arg_name, arg_value))
            continue

        # 转换失败时，会抛出异常
        # noinspection PyBroadException
        try:
            # 当 arg_value 是字符串，arg_spec的类型是对象时，尝试解析成 json
            if arg_spec.annotation in (dict, list) and isinstance(arg_value, str):
                # noinspection PyBroadException
                try:
                    arg_value = json.loads(arg_value)
                except Exception:
                    # 此处的异常直接忽略即可
                    request.context.logger.warning(
                        'Value for "%s!%s" may be incorrect: %s' % (func.__name__, arg_name, arg_value))

                # 类型一致，直接使用
                if isinstance(arg_value, arg_spec.annotation):
                    actual_args[arg_name] = arg_value
                    used_args.append(arg_name)
                    continue
            actual_args[arg_name] = arg_spec.annotation(arg_value)
            used_args.append(arg_name)
        except Exception:
            msg = 'Argument type of "%s" mismatch, expect type "%s" but got "%s", signature: (%s)' \
                  % (arg_name, arg_spec.annotation.__name__, type(arg_value).__name__, _get_parameter_str(args))
            request.context.logger.warning(msg)
            return HttpResponseBadRequest(msg)

    if not has_variable_args:
        return actual_args

    # 填充可变参数
    variable_args = {}
    for item in arg_source:
        if item in used_args:
            continue
        variable_args[item] = arg_source[item]

    # noinspection PyUnresolvedReferences
    if isinstance(request.BODY, dict):
        for item in request.BODY:
            if item in used_args:
                continue
            # noinspection PyUnresolvedReferences
            variable_args[item] = request.BODY[item]

    actual_args.update(variable_args)

    return actual_args


def _wrap_http_response(mgr, data):
    """
    将数据包装成 HttpResponse 返回
    :param data:
    :return:
    """

    # 处理返回函数
    data = mgr.process_return(data)

    if data is None:
        return HttpResponse()

    if isinstance(data, HttpResponse):
        return data

    if isinstance(data, bool):
        return HttpResponse('true' if bool else 'false')

    if isinstance(data, (dict, list, set, tuple)):
        return JsonResponse(data)

    if isinstance(data, str):
        return HttpResponse(data.encode())

    if isinstance(data, bytes):
        return HttpResponse(data)

    return HttpResponse(str(data).encode())


class HttpResponseUnauthorized(HttpResponse):
    status_code = 401
