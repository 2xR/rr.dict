"""This module contains functions to simplify some tasks that appear somewhat frequently when
working with dictionaries.
"""
import enum
import math

__version__ = "0.2.0"
__author__ = "Rui Rei"
__copyright__ = "Copyright 2017 {author}".format(author=__author__)
__license__ = "MIT"


class Undefined(enum.Enum):
    UNDEFINED = enum.auto()

    def __repr__(self):
        return self.name

    __str__ = __repr__


# This constant is useful to represent missing values when None could be interpreted as valid.
UNDEFINED = Undefined.UNDEFINED


def lookup(d, *ks, default=UNDEFINED):
    """Look up all the keys from `ks` in the dictionary `d`, in order.

    Returns the value associated with the first key that is found in `d`. If none of the keys are
    found, `default` is returned if given, otherwise a LookupError is raised.
    """
    for k in ks:
        v = d.get(k, UNDEFINED)
        if v is not UNDEFINED:
            return v
    if default is not UNDEFINED:
        return default
    raise LookupError("unable to find any of {}".format(", ".join(map(repr, ks))))


def extract(d, *ks, fill_missing=UNDEFINED, skip_missing=False):
    """Create a dictionary by only extracting the keys in `ks` from `d`.

    Missing keys can be handled in three ways:

    1) if `fill_missing` is given, missing keys are added anyway with the given value associated.
    2) if `skip_missing` is true, missing keys in `d` are not added to the result dict.
    3) otherwise, `KeyError` is raised if any key is missing.
    """
    r = {}
    for k in ks:
        v = d.get(k, fill_missing)
        if v is not UNDEFINED:
            r[k] = v
        elif not skip_missing:
            raise KeyError(k)
    return r


def invert(d):
    """Given a dictionary `d`, produce a dictionary that inverts its key-value relationship.

    Warning:
        If a value appears multiple times in `d` the resulting inverse dictionary will contain
        only the last key that was encountered while iterating over `d` (which is, by definition,
        undefined ;-).
    """
    return {v: k for k, v in d.items()}


def merge(*ds, depth=math.inf):
    """Shallow or deep merge an arbitrary number of dictionaries.

    Note that dicts appearing later in the argument list will possibly overwrite values from
    earlier dicts. The merge can be shallow (equivalent to using `.update()` multiple times on a
    result dict) or arbitrarily deep depending on the `depth` parameter (default is infinite
    depth).

    Returns:
        A new dictionary containing the result of the merge operation.
    """
    r = {}
    for d in ds:
        r = combine(r, d, _merge_combinator, depth=depth, symmetric=True)
    return r


def diff(d0, d1, depth=math.inf, symmetric=True):
    """Compute a difference between dictionaries `d0` and `d1`.

    There are several ways in which a difference can be computed. The two features of the
    difference considered by this function are shallow *vs* deep diff and symmetric *vs*
    asymmetric diff.
    """
    combinator = _symmetric_diff_combinator if symmetric else _asymmetric_diff_combinator
    return combine(d0, d1, combinator, depth=depth, symmetric=symmetric)


def combine(d0, d1, combinator, depth=math.inf, symmetric=True):
    """Combine two dictionaries using a given `combinator()` function.

    This function produces a new dictionary `d2` that contains keys from `d0` or `d1`; for a
    given key `k`, it is mapped to the result of the `combinator()` function called with three
    arguments:

    - the sequence of keys up to the current location (including `k`); this is always a 1-item
    sequence in shallow operations but may contain longer sequences of keys in deep operations
    where the dictionaries are recursively traversed.

    - the respective values for `k` in `d0` and `d1`. When `k` is not found in either operand
    dict, it is replaced with the constant `UNDEFINED` in the call to `combinator()`.

    If `combinator()` returns `UNDEFINED`, then `k` is not added to the resulting dictionary
    `d2`. The above behavior roughly translates to the following code:

        v2 = combinator(ks+(k,), d0.get(k, UNDEFINED), d1.get(k, UNDEFINED))
        if v2 is not UNDEFINED:
            d2[k] = v2

    The `depth` parameter controls how many levels of nested dictionaries are traversed before
    stopping recursion.

    If `symmetric` is false, then the `combinator()` function is called only for all keys in `d0`
    (regardless of their presence in `d1`). If `symmetric` is enabled, then `combinator()` is
    also called for all keys that belong to `d1` but not to `d0`, allowing a full coverage of the
    two dictionaries.

    See `merge()` and `diff()` for example usages of this function.

    Recursive implementation
    ------------------------

    This function is naturally implemented using recursion. However, there is a limitation on the
    size of the Python implementation's stack; to circumvent this limitation, we transformed the
    recursive implementation into an iterative one. The only real advantage to this is the
    ability to deal with very deeply nested dictionaries. The code is a lot more complex though.
    For reference, we keep the recursive implementation below:

    def combine(d0, d1, combinator, ks=(), depth=math.inf, symmetric=True):
        d2 = {}
        for k, v0 in d0.items():
            v1 = d1.get(k, UNDEFINED)
            if len(ks) < depth and isinstance(v0, dict) and isinstance(v1, dict):
                v2 = combine(v0, v1, combinator, ks+(k,), depth, symmetric)
                if len(v2) > 0:
                    d2[k] = v2
            else:
                v2 = combinator(ks+(k,), v0, v1)
                if v2 is not UNDEFINED:
                    d2[k] = v2
        # If `symmetric` is enabled, we must process keys which **appear in `d1` but not in
        # `d0`**. This is because we already processed all the keys in `d0` in the loop above.
        if symmetric:
            for k, v1 in d1.items():
                if k not in d0:
                    v2 = combinator(ks+(k,), UNDEFINED, v1)
                    if v2 is not UNDEFINED:
                        d2[k] = v2
        return d2
    """
    # We circumvent python's stack limit by managing a call stack ourselves.
    # WARNING: iter() is necessary because item view objects can be iterated multiple times!
    stack = [((), iter(d0.items()), iter(d1.items()), d0, d1, {})]
    while True:
        ks, i0, i1, d0, d1, d2 = stack[-1]
        recurse = False
        for k, v0 in i0:
            v1 = d1.get(k, UNDEFINED)
            if len(ks) < depth and isinstance(v0, dict) and isinstance(v1, dict):
                stack.append((ks+(k,), iter(v0.items()), iter(v1.items()), v0, v1, {}))
                recurse = True
                break
            else:
                v2 = combinator(ks, v0, v1)
                if v2 is not UNDEFINED:
                    d2[k] = v2
        if recurse:
            continue
        # If `symmetric` is enabled, we must process keys which **appear in `d1` but not in
        # `d0`**. This is because we already processed all the keys in `d0` in the loop above.
        if symmetric:
            for k, v1 in i1:
                if k not in d0:
                    v2 = combinator(ks, UNDEFINED, v1)
                    if v2 is not UNDEFINED:
                        d2[k] = v2
        stack.pop()
        if len(stack) == 0:
            return d2
        # If we're "returning" from a recursive call and the return value is a non-empty dict,
        # we should connect it to the return value of the parent frame.
        if len(d2) > 0:
            d2_parent = stack[-1][-1]
            d2_parent[ks[-1]] = d2


def _merge_combinator(ks, v0, v1):
    """Combinator function used in dict merge operations.

    Returns the value in the first dict if the second dict does not define a value for the
    corresponding key, otherwise returns the second value. This corresponds to preserving the
    default value but allowing it to be overridden in the second dictionary.
    """
    return v0 if v1 is UNDEFINED else v1


def _asymmetric_diff_combinator(ks, v0, v1):
    """Combinator function used in asymmetric dict diffs.

    Simply compares the two values with the equality operator, and returns the first value
    (corresponding to the first dict in the diff call) in case they're different.
    """
    return UNDEFINED if v0 == v1 else v0


def _symmetric_diff_combinator(ks, v0, v1):
    """Combinator function used in symmetric dict diffs.

    Simply compares the two values with the equality operator, and returns a tuple containing the
    two values in case they're different.
    """
    return UNDEFINED if v0 == v1 else (v0, v1)
