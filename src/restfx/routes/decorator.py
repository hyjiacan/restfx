import json
from collections import OrderedDict
from functools import wraps, partial
from typing import Tuple, Union

import settings
from .validator import Validator
from ..config import AppConfig
from ..http import HttpRequest, HttpServerError
from ..http import HttpResponse, HttpBadRequest, JsonResponse
from ..routes.meta import RouteMeta
from ..session import HttpSession
from ..util import Logger
from ..util.func_util import ArgumentSpecification, get_func_info


def route(module=None, name=None, extname=None, validators: Union[Tuple[Validator], Validator] = None, **kwargs):
    """
    用于控制路由的访问权限，路由均需要添加此装饰器，若未添加，则不可访问
    用法：
    @route('用户管理', '编辑用户')
    def get(req):
        pass
    :param module: str 路由所属模块，一般在查询权限时会用到
    :param name: str 路由名称，一般在查询权限时会用到
    :param extname: 给路径指定一个扩展名，不能包含 . 符号
    :param validators: 指定参数应用的校验规则，每个需要校验的参数为元组的一个项
    """

    # 支持错误的元组写法: (aaa)
    # 正确写法应该为: (aaa,)
    if not isinstance(validators, tuple) and validators is not None:
        validators = (validators,)

    def invoke_route(handler):
        @wraps(handler)
        def caller(*args):
            # 参数长度不为 2 时，认为是用户调用
            if len(args) != 2:
                return handler(*args)

            # Http 请求对象
            # :type HttpRequest
            request = args[0]
            # 函数声明时定义的参数列表
            # :type OrderedDict
            handler_args = args[1]

            # 如果传入的参数第一个不是 request，第二个不是 OrderedDict，
            # 那么就认为是用户调用，而不是路由调用
            # 此时直接将原参数传给 handler 进行调用
            if not isinstance(request, HttpRequest) or not isinstance(handler_args, OrderedDict):
                return handler(*args)

            config = AppConfig.get(request.app_id)

            meta = RouteMeta(
                handler,
                handler_args,
                route_id='%s_%s' % (handler.__module__.replace('_', '__').replace('.', '_'), handler.__name__),
                module=module,
                name=name,
                extname=extname,
                method=request.method,
                path=request.path,
                kwargs=kwargs,
            )

            return _invoke_with_route(request, meta, config, validators)

        return caller

    return invoke_route


def validate_args(func, validators: Tuple[Validator], args: dict):
    if not validators:
        return True

    if not args:
        return True

    param_name = None
    result = None
    for validator in validators:
        param_name = validator._param_name
        result = validator.validate(args)
        if result is None:
            continue
        break
    if result is None:
        return result

    if settings.DEBUG:
        func_info = get_func_info(func)
        return '%s\n\tFailed to validate parameter "%s": %s' % (
            func_info,
            param_name,
            result
        )

    return 'Failed to validate parameter "%s": %s' % (
        param_name,
        result
    )


def _invoke_with_route(request: HttpRequest, meta: RouteMeta, config: AppConfig, validators: tuple):
    handler_args = meta.handler_args
    func = meta.handler

    mgr = config.middleware_manager

    # 处理请求中的json参数
    _process_json_args(request, config)

    # 调用中间件，以处理请求
    result = mgr.handle_request(request, meta)

    # 使用函数代理，减少相同调用的参数传递
    handle_response = partial(mgr.handle_response, request, meta)
    wrap_response = partial(_wrap_http_response, mgr, request, meta)

    # 返回了 HttpResponse，直接返回此对象
    if isinstance(result, HttpResponse):
        return handle_response(result)

    # 返回了非 None，表示停止请求，并将结果作为路由的返回值
    if result is not None:
        return handle_response(wrap_response(result))

    # 有参数，自动从 queryString, POST 或 json 中获取
    # 匹配参数
    actual_args = _get_actual_args(request, func, handler_args, config)

    # 只有解析参数出错时才会返回 HttpResponse
    # 此时中止执行
    if isinstance(actual_args, HttpResponse):
        return handle_response(actual_args)

    # 调用中间件
    result = mgr.before_invoke(request, meta, actual_args)

    # 返回了 HttpResponse ， 直接返回此对象
    if isinstance(result, HttpResponse):
        return handle_response(result)

    # 返回了非 None，表示停止请求，并将结果作为路由的返回值
    if result is not None:
        return handle_response(wrap_response(result))

    # 执行校验
    result = validate_args(func, validators, actual_args)
    if result is not None:
        return HttpBadRequest(result, content_type='text/plain')

    # 调用路由函数
    arg_len = len(handler_args)

    try:
        if arg_len == 0:
            result = func()
        else:
            result = func(**actual_args)
    except Exception as e:
        message = get_func_info(func)
        Logger.get(config.app_id).error(message, e, False)
        from restfx.util import utils
        return handle_response(HttpServerError(utils.get_exception_info(message, e)))

    return handle_response(wrap_response(result))


def _process_json_args(request: HttpRequest, config: AppConfig):
    """
    参数处理
    :return:
    """
    if request.content_type is None or 'application/json' not in request.content_type:
        return

    # 如果请求是json类型，就先处理一下

    body = request.data

    if not body:
        return

    try:
        request.BODY = json.loads(body.decode())
    except Exception as e:
        Logger.get(config.app_id).warning('Failed to deserialize request body: %s' % str(e))


def _get_parameter_str(args: OrderedDict):
    return ', '.join(filter(lambda n: n[0] != '_', [str(args[arg]) for arg in args]))


def _get_value(data: dict, name: str, arg_spec: ArgumentSpecification, backup1, backup2):
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

    if isinstance(backup1, dict):
        if name in backup1:
            return False, backup1[name]

        if alias is not None and alias in backup1:
            return False, backup1[alias]

    if isinstance(backup2, dict):
        if name in backup2:
            return False, backup2[name]

        if alias is not None and alias in backup2:
            return False, backup2[alias]

    # 使用默认值
    if arg_spec.has_default:
        return True, arg_spec.default

    # 缺少无默认值的参数
    return None, None


def _get_actual_args(request: HttpRequest, func, args: OrderedDict, config: AppConfig) -> dict or HttpResponse:
    method = request.method.lower()
    actual_args = {}

    # 已使用的参数名称，用于后期填充可变参数时作排除用
    used_args = []
    # 是否声明了可变参数
    has_variable_args = False

    # noinspection PyUnresolvedReferences
    arg_source = request.GET if method in ['delete', 'get'] else request.POST

    # 声明的注入参数集合
    injection_args = []

    for arg_name in args.keys():
        arg_spec = args.get(arg_name)

        if arg_spec.is_injection:
            injection_args.append(arg_name)
            used_args.append(arg_name)
            continue

        # 如果是可变参数：如: **kwargs
        # 设置标记，以在后面进行填充
        if arg_spec.is_variable:
            has_variable_args = True
            continue

        # 以下情况将传入 HttpRequest 对象
        # 1. 当参数名称是 request 并且未指定类型
        # 2. 当参数类型是 HttpRequest 时 (不论参数名称，包括 request)
        # 但是，参数名称是 request 但其类型不是 HttpRequest ，就会被当作一般参数处理
        if arg_name == 'request' and not arg_spec.has_annotation:
            actual_args[arg_name] = request
            continue
        if arg_spec.annotation == HttpRequest:
            actual_args[arg_name] = request
            continue

        # 以下情况将传入 HttpSession 对象
        # 1. 当参数名称是 session 并且未指定类型
        # 2. 当参数类型是 HttpSession 时 (不论参数名称，包括 session)
        # 但是，参数名称是 session 但其类型不是 HttpSession ，就会被当作一般参数处理
        is_session = False
        if arg_name == 'request' and not arg_spec.has_annotation:
            is_session = True
        elif arg_spec.annotation == HttpSession:
            is_session = True

        if is_session:
            if request.session is None:
                msg = '%s\n\tParameter "%s" of type "HttpSession" is not available, ' \
                      'the value will always be "None", ' \
                      'please make sure that you have registered the Session-Middleware correctly, ' \
                      'Parameters: (%s)' % (
                          get_func_info(func),
                          arg_name,
                          _get_parameter_str(args)
                      )
                Logger.get(config.app_id).warning(msg)
            # 在 session 未启用时，其值为 None
            actual_args[arg_name] = request.session
            continue

        # noinspection PyUnresolvedReferences
        use_default, arg_value = _get_value(arg_source, arg_name, arg_spec, request.BODY, request.FILES)

        # 未找到参数
        if use_default is None:
            msg = 'Missing required argument "%s".' % arg_name
            Logger.get(config.app_id).warning(msg)
            return HttpBadRequest(msg)

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
                continue
            if arg_value == 'false':
                actual_args[arg_name] = False
                used_args.append(arg_name)
                continue

            msg = 'Cannot parse value "%s" into type "%s: %s". (expected: true/false)' % (
                (arg_value, arg_spec.annotation_name, arg_name))
            Logger.get(config.app_id).warning(msg)
            return HttpBadRequest(msg)

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
                    msg = 'Cannot parse value "%s" into type "%s": %s.' % (
                        arg_value, arg_spec.annotation_name, arg_name
                    )
                    Logger.get(config.app_id).warning(msg)
                    return HttpBadRequest(msg)

            # 类型一致，直接使用
            if isinstance(arg_value, arg_spec.annotation):
                # 如果原始声明是 tuple 类型，那么把 list 转换成 tuple
                # 虽然在发起请求的时候并不能指定为 tuple，但还是想兼容一下
                actual_args[arg_name] = tuple(arg_value) if arg_spec.is_tuple else arg_value
                used_args.append(arg_name)
                continue
            actual_args[arg_name] = arg_spec.annotation(arg_value)
            used_args.append(arg_name)
        except Exception:
            msg = 'Cannot parse value "%s" into type "%s": %s.' % (
                arg_value, arg_spec.annotation_name, arg_name
            )
            Logger.get(config.app_id).warning(msg)
            return HttpBadRequest(msg)

    # 填充注入参数
    for arg_name in injection_args:
        # 注入名称不包含前缀 _
        # 所以要 [1:]
        injection_name = arg_name[1:]
        if injection_name in request._injections:
            actual_args[arg_name] = request._injections[injection_name]
        elif injection_name in config.injections:
            actual_args[arg_name] = config.injections[injection_name]
        else:
            msg = 'Injection name "%s" not found.' % injection_name
            if config.debug:
                msg = '%s\n\t%s' % (get_func_info(func), msg)
            Logger.get(config.app_id).error(msg)
            return HttpServerError(msg) if config.debug else HttpServerError()

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

    variable_arg_keys = variable_args.keys()

    # 没有可变参数
    if not variable_arg_keys:
        return actual_args

    # 有可变参数，并且指定了 kwargs
    if has_variable_args:
        actual_args.update(variable_args)
        return actual_args

    # 有可变参数，并且未指定 kwargs
    # 未启用严格模式
    if config.strict_mode is not True:
        return actual_args

    # 启用了严格模式
    # 返回 400 响应
    msg = 'Unknown argument(s) found: "%s", Parameters: (%s).' \
          % (','.join(variable_arg_keys), _get_parameter_str(args))
    Logger.get(config.app_id).warning(msg)
    if not config.debug:
        msg = 'Unknown argument(s) found: %s.' % ','.join(variable_arg_keys)
    return HttpBadRequest(msg)


def _wrap_http_response(mgr, request, meta, data):
    """
    将数据包装成 HttpResponse 返回
    :param data:
    :return:
    """

    # 调用中间件，处理返回函数
    data = mgr.after_return(request, meta, data)

    if data is None:
        return HttpResponse()

    if isinstance(data, HttpResponse):
        return data

    if isinstance(data, bool):
        return HttpResponse('true' if bool else 'false', content_type='text/plain')

    if isinstance(data, (dict, list, set, tuple)):
        return JsonResponse(data)

    if isinstance(data, str):
        return HttpResponse(data.encode(), content_type='text/plain')

    if isinstance(data, bytes):
        return HttpResponse(data, content_type='application/octet-stream')

    return HttpResponse(str(data).encode(), content_type='text/plain')
