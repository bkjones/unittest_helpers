from contextlib2 import contextmanager, ExitStack
from mock import patch


@contextmanager
def remove_decorator(func, remove_all_decorators=False):
    """ Remove the last applied decorator from the function passed and return
    the original, undecorated function.  If ``remove_all_decorators`` is set
    to True then every decorator that has been applied to the function will
    be removed, including timers and context managers.

        :note: This does not modify the passed function, it simply retrieves
            the original function from within the decorated one.

        :returns: Function without the last applied decorator
    """

    # If the function object has a closure object then try to recover
    # undecorated function
    if hasattr(func, '__closure__') and func.__closure__:
        # The cell contents of the closure is the original functions
        closure = func.__closure__[0]
        undecorated_func = closure.cell_contents

        while remove_all_decorators and hasattr(undecorated_func, '__closure__'):
            closure = func.__closure__[0]
            undecorated_func = closure.cell_contents

        # Return the undecorated function to the with statement block
        # After the __exit__ function is called the originally decorated
        # function will be in place once again
        yield undecorated_func
    else:
        yield func


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
