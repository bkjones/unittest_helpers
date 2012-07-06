from contextlib2 import contextmanager, ExitStack
from mock import patch

class KeyLookupCountError(Exception):
    """Raised when a key in MockDict is looked up some number of times
    different from how many are expected/asserted.

    """

class MockDict(dict):
    def __init__(self, *args, **kwargs):
        self.key_lookups = list()
        self.updates = list()
        super(MockDict, self).__init__(*args, **kwargs)
        for arg in args:


    def __getitem__(self, item):
        self.key_lookups.append(item)
        return super(MockDict, self).__getitem__(item)

    def __setitem__(self, item, value):
        self.updates.append((item, value))
        if isinstance(value, dict):
            value = MockDict(value)
        return super(MockDict, self).__setitem__(item, value)

    def assert_key_looked_up_once(self, key):
        actual_lookup_count = self.key_lookups.count(key)
        try:
            assert actual_lookup_count == 1
        except AssertionError:
            raise KeyLookupCountError("Expected %s to be looked up once, but was looked up %s times" % (key, actual_lookup_count))


@contextmanager
def patches(*args):
    stack = ExitStack()
    for thing in args:
        name = thing.split('.')[-1]
        new_patch = patch(thing)
        triggered_patch = stack.enter_context(new_patch)
        setattr(stack, name, triggered_patch)

    yield stack
