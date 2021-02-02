from restfx import route


@route('module-name', 'route-name-GET')
def get(_root, request, **kwargs):
    return {
        'args': kwargs,
        'project_root': _root
    }


@route('module-name', 'route-name-POST')
def post(request, **kwargs):
    return kwargs


@route('module-name', 'route-name-DELETE')
def delete(request, **kwargs):
    return kwargs
