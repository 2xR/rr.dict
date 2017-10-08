"""This module provides some functions for creating and managing nested dictionaries.

The recommended use of this module is to import the module and access all functions through the
module object, like so:

    import rr.dict.nested as nesteddict
    from pprint import pprint

    d = {}
    nesteddict.set(d, 1, 2, 3)
    nesteddict.set(d, 1, 5, 4, 6)
    pprint(d)
"""
from . import UNDEFINED


def new(items=()):
    """Create a new nested dict from `items`.

    Each element in `items` is expected to be an iterable containing a sequence of keys followed
    by a value at the end.
    """
    return update(dict(), items)


def copy(d, depth=None):
    """Create a deep-ish copy of a nested dict.

    See `items()` for more information on the `depth` parameter.
    """
    return update(type(d)(), items(d, depth=depth))


def update(d, items):
    """Add a set of `items` to the nested dict `d`.

    Each element in `items` is expected to be an iterable containing a sequence of keys followed
    by a value at the end.
    """
    for item in items:
        set(d, *item)
    return d


def get(d, *keys, default=UNDEFINED):
    """Get a value from the nested dictionary.

    If the given path does not exist in the nested dict, the `default` value is returned if one
    was given, otherwise a KeyError is raised for the first key that was not found.
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


def set(d, *item):
    """Set a value in the nested dict `d`.

    Any subdictionaries created in this process are of the same type as `d`. Note that this
    implies the requirement that `d`s type have a zero-argument constructor.
    """
    *intermediate_keys, last_key, value = item
    create_intermediate_dicts = False
    cls = type(d)
    for k in intermediate_keys:
        if create_intermediate_dicts:
            d[k] = d = cls()
            continue
        try:
            d = d[k]
        except KeyError:
            d[k] = d = cls()
            create_intermediate_dicts = True
    d[last_key] = value
    return value


def setdefault(d, *item):
    """Works like `dict.setdefault()`, but for nested dicts.

    Returns `get(d, *item[:-1])`, and if the path does not exist, it is created and the default
    value `item[-1]` is set.
    """
    try:
        return get(d, *item[:-1])
    except KeyError:
        return set(d, *item)


def pop(d, *keys):
    """Remove an item from the nested dict and return its value."""
    return get(d, *keys[:-1]).pop(keys[-1])


def pop_path(d, *keys):
    """Like `pop()`, but deletes any dicts in the path that become empty after the removal."""
    dicts = []
    for k in keys[:-1]:
        dicts.append(d)
        d = d[k]
    value = d.pop(keys[-1])
    for k in reversed(keys[:-1]):
        d = dicts.pop()
        if len(d[k]) == 0:
            del d[k]
        else:
            break
    return value


# set up some aliases for pop() and pop_path()
remove = pop
remove_path = pop_path


def items(d, depth=None):
    """An iterator over the items in the nested dict `d`.

    This generator produces items (tuples) consisting of at most `depth` keys plus a value. If a
    depth is not specified, then it will iterate over all the leaves of the nested dict,
    otherwise recursion is halted when the keyset's length equals `depth`.
    """
    stack = [iter(d.items())]  # use iter() because dict views can be iterated multiple times
    item = []
    while True:
        iterator = stack[-1]
        for key, value in iterator:
            item.append(key)
            if isinstance(value, dict) and (depth is None or len(item) < depth):
                stack.append(iter(value.items()))
                break
            item.append(value)
            yield tuple(item)
            item.pop()
            item.pop()
        else:
            stack.pop()
            if len(stack) == 0:
                return
            item.pop()
