import sys
from functools import partial

from werkzeug.local import LocalProxy
from werkzeug.local import LocalStack

from restfx.http import HttpRequest

_request_ctx_err_msg = """\
Working outside of request context.

This typically means that you attempted to use functionality that needed
an active HTTP request.  Consult the documentation on testing for
information about how to avoid this problem.\
"""
_app_ctx_err_msg = """\
Working outside of application context.

This typically means that you attempted to use functionality that needed
to interface with the current application object in some way. To solve
this, set up an application context with app.app_context().  See the
documentation for more information.\
"""


def _lookup_req_object(name):
    top = _request_ctx_stack.top
    if top is None:
        raise RuntimeError(_request_ctx_err_msg)
    return getattr(top, name)


def _lookup_app_object(name):
    top = _app_ctx_stack.top
    if top is None:
        raise RuntimeError(_app_ctx_err_msg)
    return getattr(top, name)


def _find_app():
    top = _app_ctx_stack.top
    if top is None:
        raise RuntimeError(_app_ctx_err_msg)
    return top.app


# context locals
_request_ctx_stack = LocalStack()
_app_ctx_stack = LocalStack()
current_app = LocalProxy(_find_app)
current_request = LocalProxy(partial(_lookup_req_object, "request"))
current_session = LocalProxy(partial(_lookup_req_object, "session"))
g = LocalProxy(partial(_lookup_app_object, "g"))

# a singleton sentinel value for parameter defaults
_sentinel = object()


class ContextStore:
    """
    上下文中数据存储支持
    """

    def __init__(self):
        self.store = {}

    def get(self, name, default=None):
        return self.store.get(name, default)

    def pop(self, name, default=_sentinel):
        if default is _sentinel:
            return self.store.pop(name)
        else:
            return self.store.pop(name, default)

    def setdefault(self, name, default=None):
        return self.store.setdefault(name, default)

    def __contains__(self, item):
        return item in self.store

    def __iter__(self):
        return iter(self.store)

    def __repr__(self):
        top = _app_ctx_stack.top
        if top is not None:
            return "<restfx.g of %r>" % top.app.id
        return object.__repr__(self)


class AppContext:
    def __init__(self, app):
        self.app = app
        self.store = ContextStore()
        # Like request context, app contexts can be pushed multiple times
        # but there a basic "refcount" is enough to track them.
        # self._refcnt = 0

    def push(self):
        """Binds the app context to the current context."""
        # self._refcnt += 1
        _app_ctx_stack.push(self)

    def pop(self, exc=_sentinel):
        rv = _app_ctx_stack.pop()
        assert rv is self, "Popped wrong app context.  (%r instead of %r)" % (rv, self)

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.pop(exc_value)


class RequestContext:
    def __init__(self, app, environ):
        self.app = app
        self.request = HttpRequest(environ, app.id)
        # self.session = session
        self.store = ContextStore()
        # Request contexts can be pushed multiple times and interleaved with
        # other request contexts.  Now only if the last level is popped we
        # get rid of them.  Additionally if an application context is missing
        # one is created implicitly so for each level we add this information
        self._implicit_app_ctx_stack = []

    def push(self):
        # Before we push the request context we have to ensure that there
        # is an application context.
        app_ctx = _app_ctx_stack.top
        if app_ctx is None or app_ctx.app != self.app:
            app_ctx = self.app.context()
            app_ctx.push()
            self._implicit_app_ctx_stack.append(app_ctx)
        else:
            self._implicit_app_ctx_stack.append(None)

        _request_ctx_stack.push(self)

        # Open the session at the moment that the request context is available.
        # This allows a custom open_session method to use the request context.
        # Only open a new session if this is the first time the request was
        # pushed, otherwise stream_with_context loses the session.
        if self.session is None:
            session_interface = self.app.session_interface
            self.session = session_interface.open_session(self.app, self.request)

            if self.session is None:
                self.session = session_interface.make_null_session(self.app)

    def pop(self, exc=_sentinel):
        """Pops the request context and unbinds it by doing that.  This will
        also trigger the execution of functions registered by the
        :meth:`~flask.Flask.teardown_request` decorator.

        .. versionchanged:: 0.9
           Added the `exc` argument.
        """
        app_ctx = self._implicit_app_ctx_stack.pop()
        clear_request = False

        try:
            if not self._implicit_app_ctx_stack:
                self.preserved = False
                self._preserved_exc = None
                if exc is _sentinel:
                    exc = sys.exc_info()[1]
                self.app.do_teardown_request(exc)

                request_close = getattr(self.request, "close", None)
                if request_close is not None:
                    request_close()
                clear_request = True
        finally:
            rv = _request_ctx_stack.pop()

            # get rid of circular dependencies at the end of the request
            # so that we don't require the GC to be active.
            if clear_request:
                rv.request.environ["werkzeug.request"] = None

            # Get rid of the app as well if necessary.
            if app_ctx is not None:
                app_ctx.pop(exc)

            assert (
                    rv is self
            ), "Popped wrong request context. (%r instead of %r)" % (rv, self)

    def auto_pop(self, exc):
        if self.request.environ.get("flask._preserve_context") or (
                exc is not None and self.app.preserve_context_on_exception
        ):
            self.preserved = True
            self._preserved_exc = exc
        else:
            self.pop(exc)

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        # do not pop the request stack if we are in debug mode and an
        # exception happened.  This will allow the debugger to still
        # access the request object in the interactive shell.  Furthermore
        # the context can be force kept alive for the test client.
        # See flask.testing for how this works.
        self.auto_pop(exc_value)

    def __repr__(self):
        return ("<%s %r [%s] of %s>" % (
            type(self).__name__, self.request.url, self.request.method, self.app.name
        ))
