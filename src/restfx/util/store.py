# a singleton sentinel value for parameter defaults
_sentinel = object()


class ContextStore:
    """
    上下文中数据存储支持
    """

    def __init__(self, ctx_stack):
        self.store = {}
        self.ctx_stack = ctx_stack

    def get(self, name, default=None):
        return self.store.get(name, default)

    def pop(self, name, default=_sentinel):
        if default is _sentinel:
            return self.store.pop(name)
        else:
            return self.store.pop(name, default)

    def setdefault(self, name, default=None):
        return self.store.setdefault(name, default)

    def update(self, items: dict):
        self.store.update(items)

    def __contains__(self, item):
        return item in self.store

    def __iter__(self):
        return iter(self.store)

    def __repr__(self):
        top = self.ctx_stack.top
        if top is not None:
            return "<restfx.ContextStore of %r>" % top.app.id
        return object.__repr__(self)
