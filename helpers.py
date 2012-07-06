from contextlib2 import contextmanager, ExitStack
from mock import patch


class KeyLookupCountError(Exception):
    """Raised when a key in MockDict is looked up some number of times
    different from how many are expected/asserted.

    """


class MockDict(dict):
    def __init__(self, *args, **kwargs):
        super(MockDict, self).__init__(*args, **kwargs)
        self.key_lookups = list()
        self.updates = list()

        # Since by this point we are a fully qualified dictionary object we
        # can iterate through our own keys and for any nested dictionary
        # object we can explicitly convert it and any other dictionaries
        # in its structure to a MockDict object

        for key in self:
            value = self[key]
            if self._is_valid_dict(value):
                self[key] = MockDict(value)

    def _is_valid_dict(self, val):
        """ :returns: True iff the value passed is an instance or subclass of
                dict and not yet a MockDict object.

            We use isinstance here instead of type dict to take into account
            a user may have dictionary subclasses or dict-like objects that we
            should still support.  Using type instead would restrict us to the
            base dictionary type.
        """
        return isinstance(val, dict) and not isinstance(val, MockDict)

    def __getitem__(self, item):
        self.key_lookups.append(item)
        return super(MockDict, self).__getitem__(item)

    def __setitem__(self, item, value):
        self.updates.append((item, value))
        if self._is_valid_dict(value):
            value = MockDict(value)
        return super(MockDict, self).__setitem__(item, value)

    def assert_key_looked_up_once(self, key):
        actual_lookup_count = self.key_lookups.count(key)
        try:
            assert actual_lookup_count == 1
        except AssertionError:
            raise KeyLookupCountError(
                "Expected {0} to be looked up once, but was looked up {1} times".
                format(key, actual_lookup_count)
            )


@contextmanager
def patches(*args):
    stack = ExitStack()
    for thing in args:
        name = thing.split('.')[-1]
        new_patch = patch(thing)
        triggered_patch = stack.enter_context(new_patch)
        setattr(stack, name, triggered_patch)

    yield stack
