"""This module provides some functions for creating and managing nested dictionaries arranged in
a tree structure, i.e. dictionaries containing other dictionaries as values, and so on...

The intended use of this module is to import the module and access all functions through the module
object, like so:

    import rr.dict.nested as treedict
    from pprint import pprint

    d = {}
    treedict.set(d, 1, 2, 3)
    treedict.set(d, 1, 5, 4, 6)
    pprint(d)
"""
from . import UNDEFINED


def new(iterable=()):
    """Create a new tree dict from `iterable`."""
    d = dict()
    update(d, iterable)
    return d


def update(d, iterable):
    """Add a set of items from `iterable` to the tree dict `d`.

    Each item in `iterable` is expected to be an iterable containing a sequence of keys followed
    by a value at the end.
    """
    for item in iterable:
        set(d, *item)
    return d


def get(d, keys, default=UNDEFINED):
    """Get a nested value from the tree dictionary.

    If the given path does not exist in the tree dict, the `default` value (keyword-only argument
    to this function) is returned.
    """
    try:
        for k in keys:
            d = d[k]
        return d
    except KeyError:
        if default is UNDEFINED:
            raise
        return default


def has(d, *keys):
    """True iff the given keyset exists in `d`."""
    try:
        get(d, *keys)
        return True
    except KeyError:
        return False


def set(d, *intermediate_keys, last_key, value):
    """Set a nested value in the tree dict `d`.

    Any subdictionaries created in this process are of the same type as `d`. Note that this
    implies a requirement that `d`s type has a zero-argument constructor.
    """
    cls = type(d)
    intermediate_keys = iter(intermediate_keys)
    for k in intermediate_keys:
        try:
            d = d[k]
        except KeyError:
            d = d[k] = cls()
            for k in intermediate_keys:
                d = d[k] = cls()
            break
    d[last_key] = value
    return value


def setdefault(D, *path_plus_default):
    """Like dict.setdefault(), returns treedict.get(D, *path). If the path does not exist, it is
    created and the default value is set."""
    path = path_plus_default[:-1]
    try:
        return get(D, *path)
    except KeyError:
        return set(D, *path_plus_default)


def pop(D, *path):
    D = get(D, *path[:-1])
    return D.pop(path[-1])


def pop_path(D, *path):
    """Same as treedict.pop(), but deletes the dictionaries in the path if they become empty
    after the removal of the item."""
    dicts = []
    for elem in path[:-1]:
        dicts.append(D)
        D = D[elem]
    value = D.pop(path[-1])
    for elem in reversed(path[:-1]):
        D = dicts.pop()
        if len(D[elem]) == 0:
            del D[elem]
        else:
            break
    return value

# set up some aliases for pop() and pop_path()
remove = pop
remove_path = pop_path


def items(D, depth=None):
    stack = [D.items()]
    path = []
    while len(stack) > 0:
        iterator = stack[-1]
        for key, value in iterator:
            path.append(key)
            if isinstance(value, dict) and (depth is None or len(path) < depth):
                stack.append(value.items())
                break
            path.append(value)
            yield tuple(path)
            path.pop()
            path.pop()
        # pop stack if the for loop above has run till the end
        if iterator is stack[-1]:
            stack.pop()
            if len(path) > 0:
                path.pop()


def copy(D, depth=None):
    clone = type(D)()
    update(clone, items(D, depth))
    return clone
