from functools import wraps
import inspect


def inidecorator(func):
    """
    Automatically assigns the parameters.

    >>> class process:
    ...     @inidecorator
    ...     def __init__(self, cmd, reachable=False, user='root'):
    ...         pass
    >>> p = process('halt', True)
    >>> p.cmd, p.reachable, p.user
    ('halt', True, 'root')
    """
    names, varargs, keywords, defaults = inspect.getargspec(func)

    @wraps(func)
    def wrapper(self, *args, **kargs):
        for name, arg in list(zip(names[1:], args)) + list(kargs.items()):
            setattr(self, "_" + name, arg)

        for name, default in zip(reversed(names), reversed(defaults)):
            if not hasattr(self, "_" + name):
                setattr(self, "_" + name, default)

        func(self, *args, **kargs)

    return wrapper
