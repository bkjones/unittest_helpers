from contextlib2 import contextmanager, ExitStack
from mock import patch


def remove_decorator(decorated_func, remove_all_decorators=False):
    """ Remove the last applied decorator from the function passed and return
    the original, undecorated function.  If ``remove_all_decorators`` is set
    to True then every decorator that has been applied to the function will
    be removed, including timers and context managers.

        :returns: Function without the last applied decorator
    """

    # If the function object doesn't have a closure object then it hasnt been
    # decorated, so just ignore it.
    if not hasattr(decorated_func, '__closure__') or not decorated_func.__closure__:
        return decorated_func

    # The cell contents of the closure is the original functions
    closure = decorated_func.__closure__[0]
    original_func = closure.cell_contents

    if hasattr(decorated_func, '_previously_decorated_function'):
        # If we are recursing then we need to retain the original function
        # and not overwrite it each time we recurse
        original_func._previously_decorated_function = \
                         decorated_func._previously_decorated_function
    else:
        original_func._previously_decorated_function = decorated_func

    if remove_all_decorators and hasattr(original_func, '__closure__'):
        return remove_decorator(original_func, remove_all_decorators)
    else:
        return original_func


def restore_decorator(undecorated_func):
    if not hasattr(undecorated_func, '_previously_decorated_function'):
        return undecorated_func
    else:
        return getattr(undecorated_func, '_previously_decorated_function')


@contextmanager
def patches(*args):
    """A context manager for performing lots of patches at once.

    This returns an ExitStack instance that also has handles to all of the
    patched objects so they can be configured prior to execution of code
    under test.

    For example:

    stuff_to_patch = ['mymod.mycls', 'urllib.urlopen', 'whatever.here']
    with patches(stuff_to_patch) as self.patched:
        self.patched.urlopen.side_effect = Exception('Boom!')
        self.patched.mycls.some_method.return_value = True

    """
    stack = ExitStack()
    for thing in args:
        name = thing.split('.')[-1]
        new_patch = patch(thing)
        triggered_patch = stack.enter_context(new_patch)
        setattr(stack, name, triggered_patch)

    yield stack
