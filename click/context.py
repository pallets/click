class _Stack(object):
    def __init__(self):
        self._stack = []

    @property
    def top(self):
        return self._stack[-1]

    def push(self, value):
        self._stack.append(value)

    def pop(self):
        return self._stack.pop()


class _StackProxy(object):
    def __init__(self, stack):
        object.__setattr__(self, '_click_ctx_stack', stack)

    def __bool__(self):
        try:
            self. _click_ctx_stack.top
        except IndexError:
            return False
        else:
            return True

    __nonzero__ = __bool__

    __getattr__ = lambda s, n: getattr(s._click_ctx_stack.top, n)
    __setattr__ = lambda s, n, v: setattr(s._click_ctx_stack.top, n, v)


_ctx_stack = _Stack()
ctx = _StackProxy(_ctx_stack)
