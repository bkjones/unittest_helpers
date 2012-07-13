from contextlib2 import contextmanager, ExitStack
from mock import patch


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
