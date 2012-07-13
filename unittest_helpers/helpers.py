from contextlib2 import contextmanager, ExitStack
from mock import patch

def path(path):
    """Takes in a 'pathspec' and returns a callable. The returned callable
    takes in a mapping and returns the result of looking up the path in the
    supplied mapping.

    A 'pathspec' defines a path inside of a nested structure. As a first shot,
    it might be useful to try to reuse the syntax of a slice object, overriding
    the colon character to denote a nested lookup, so:

    path('a':'b':0)

    would map to a successful nested lookup in this structure:

    {'a': {'b': [1,2,3]}

    And would return the number 1.

    """
    [('a', ('b', 1)),
    ':' = '__getitem__'
    chain = '.__getitem__'.join([path.split(':')])
    print chain



class MockDict(dict):
    """
    THIS IS NOT FINISHED OR EVEN READY FOR GENERAL USE

    Right now, usage looks like this:

    >>> D1 = MockDict()
    >>> D1['foo']
    The general idea here is to be able to implant a spy object in place
    of a more complex data structure, then run the code under test that will
    make use of it, and finally, make assertions that particular lookups were
    done on the MockDict, all without ever actually creating a stand-in
    data structure.

    So, something like this is a really simplistic example:

    def test_setup_with_config_dict():
        mymodule.myappconfig = MockDict()

        cls = mymodule.myclass() # myappconfig['host'] is looked up in __init__

        mymodule.myappconfig.assert_lookup('host')


    The above is basically already supported, but trouble arises when you
    consider the semantics of supporting assertions for nested lookups, or
    lookups involving, say, lists (e.g. myappconfig['foo']['bar'][-1]), etc.

    I have a couple of ideas to pursue before totally giving up, but one thing
    that would totally rock is some means of creating a "path object", similar
    to how the built-in 'slice()' function works for lists, it'd be good to have
    a 'path()' function that takes in some kind of lookup specification (whose
    syntax is as yet undefined) and returns a callable that would take in a
    dict and return the result of the lookup.

    If that existed, I'd be able to let the user assert lookups using that
    syntax, and the incoming path spec would open doors to validating the
    assertion in multiple ways, actually.

    Here's the gist of the 'path()' function.

    >>> D1 = {'a': {'b': 1}, 'c': {'d': {'e': [1, 2, 3]}}}
    >>> getter = path('/c/d/e/0')
    >>> getter(D1)
    1

    So then a user of MockDict could use this to do assertions like this:

    >>> D1 = MockDict()
    >>> D1['a']['b'][1] # MockDict could just create this
    18
    >>> D1.assert_lookup('/a/b/1') # MockDict does a lookup w/ 'path()' or similar.

    For now, perhaps a quick solution here is to subclass defaultdict and then
    when the code under test does a lookup, create the thing being looked up,
    perhaps keeping a count for each thing looked up. Then, when the assertion
    is done, actually perform the lookup in order to validate the assertion...?

    For now, this is kind of a hack-n-slash prototype to get some ideas down
    in code.

    """


    def __init__(self, *args, **kwargs):
        super(MockDict, self).__init__(*args, **kwargs)
        self.assertlock = False

        # Since by this point we are a fully qualified dictionary object we
        # can iterate through our own keys and for any nested dictionary
        # object we can explicitly convert it and any other dictionaries
        # in its structure to a MockDict object

        for key in self:
            value = self[key]
            if self._is_valid_dict(value):
                self[key] = MockDict(value)

    def _is_valid_dict(self, val):
        """ :returns: True if the value passed is an instance or subclass of
                dict and not yet a MockDict object.

            We use isinstance here instead of type dict to take into account
            a user may have dictionary subclasses or dict-like objects that we
            should still support.  Using type instead would restrict us to the
            base dictionary type.
        """
        return isinstance(val, dict) and not isinstance(val, MockDict)

    def __getitem__(self, item):
        try:
            retval = super(MockDict, self).__getitem__(item)
        except KeyError:
            if self.assertlock:
                self.assertlock = False
                raise AssertionError("'{0}' was never looked up. Sorry.".format(item))
            else:
                # setting this to a MockDict is optimistic. We don't
                # know that a lookup would be done on this value.
                retval = MockDict()
                self[item] = retval

        if self.assertlock:
            self.assertlock = False

        return retval

    def __setitem__(self, item, value):
        if self._is_valid_dict(value):
            value = MockDict(value)
        return super(MockDict, self).__setitem__(item, value)

    @property
    def assert_lookup(self):
        """This is a bit of a hack, really. The idea is that you
        assert a lookup using the same syntax you'd use to perform an actual
        dictionary lookup. This sets an 'assertlock' so that __getitem__ knows
        it should perform a normal dict lookup instead of a MockDict-style
        'do it and populate it if it's not there' lookup.

        """
        self.assertlock = True
        return self


@contextmanager
def patches(*args):
    stack = ExitStack()
    for thing in args:
        name = thing.split('.')[-1]
        new_patch = patch(thing)
        triggered_patch = stack.enter_context(new_patch)
        setattr(stack, name, triggered_patch)

    yield stack
