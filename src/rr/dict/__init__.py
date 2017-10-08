"""This module contains functions to simplify some tasks that appear somewhat frequently when
working with dictionaries.
"""
import enum

__version__ = "0.1.0"
__author__ = "Rui Rei"
__copyright__ = "Copyright 2017 {author}".format(author=__author__)
__license__ = "MIT"


class Undefined(enum.Enum):
    UNDEFINED = "UNDEFINED"


# This constant is useful to represent missing values when None could be interpreted as valid.
UNDEFINED = Undefined.UNDEFINED


def lookup(d, keys, default=UNDEFINED):
    """Look up all the given `keys` in `d`, in order.

    Returns the value associated with the first key that is found in `d`. If none of the keys are
    found, `default` is returned if given, otherwise a LookupError is raised.
    """
    for k in keys:
        v = d.get(k, UNDEFINED)
        if v is not UNDEFINED:
            return v
    if default is not UNDEFINED:
        return default
    raise LookupError("unable to find any of {}".format(", ".join(map(repr, keys))))


def extract(d, keys, skip_missing_keys=False):
    """Create a dictionary by only extracting the keys in `keys` from `d`.

    The `skip_missing_keys` flag can be set to silently skip missing keys, otherwise a KeyError
    is raised on the first key that is not found in `d`.
    """
    if skip_missing_keys:
        return {k: d[k] for k in keys if k in d}
    else:
        return {k: d[k] for k in keys}


def invert(d):
    """Given a dictionary `d`, produce a dictionary that inverts the key-value relationship.

    Warning:
        If a value appears multiple times in `d` the resulting inverse dictionary will contain
        only the last key that was encountered while iterating over `d` (which is, by definition,
        undefined ;-).
    """
    return {v: k for k, v in d.items()}


def merge(*dicts, deep=True):
    """Shallow or deep merge an arbitrary number of dictionaries.

    Note that dicts appearing later in the argument list will possibly overwrite values from
    earlier dicts. The merge can be shallow (equivalent to using `.update()` multiple times on a
    result dict) or deep depending on the `deep` flag (default is deep merge).
    """
    result = {}
    for d in dicts:
        result = binop(result, d, value_op=_merge_value, deep=deep, symmetric=True)
    return result


def diff(d_a, d_b, deep=True, symmetric=True):
    """Compute a difference between dictionaries `d_a` and `d_b`.

    There are various manners in which a difference can be computed. The two features of the
    difference considered by this function are shallow *vs* deep diff and symmetric *vs*
    asymmetric diff.
    """
    value_op = _symmetric_value_diff if symmetric else _asymmetric_value_diff
    return binop(d_a, d_b, value_op=value_op, deep=deep, symmetric=symmetric)


def binop(d_a, d_b, value_op, deep=True, symmetric=True):
    """Apply a binary operator to the values of two dictionaries.

    Warning:
        This is a very abstract and artificial construct that was created to generalize both diff
        and merge operations. Therefore, it is probably much more easily grasped with examples.
        See `merge()` and `diff()` for example usages of this function.

    This function produces a new dictionary `d` that contains keys from `d_a` or `d_b`; for a
    given key `k`, it is mapped to the result of the `value_op()` function called with the values
    corresponding to `k` in `d_a` and `d_b`. When `k` is not found in either operand dict,
    it is replaced with the constant `UNDEFINED` in the call to `value_op()`. If `value_op()`
    returns `UNDEFINED`, then `k` is not added to the resulting dictionary `d`. The above
    behavior translates to the following code:

        v = value_op(d_a.get(k, UNDEFINED), d_b.get(k, UNDEFINED))
        if v is not UNDEFINED:
            d[k] = v

    The `deep` flag controls whether this function is called recursively when the values on both
    dicts are also dictionaries.

    If `symmetric` is false, then the `value_op()` function is called only for all keys in `d_a`
    (regardless of their presence in `d_b`). If `symmetric` is enabled, then `value_op()` is also
    called for all keys that belong to `d_b` but not to `d_a`, allowing a full coverage of the
    two dictionaries.
    """
    d = {}
    for k, v_a in d_a.items():
        v_b = d_b.get(k, UNDEFINED)
        if deep and isinstance(v_a, dict) and isinstance(v_b, dict):
            v_d = binop(v_a, v_b, value_op, deep, symmetric)
            if len(v_d) > 0:
                d[k] = v_d
        else:
            v_d = value_op(v_a, v_b)
            if v_d is not UNDEFINED:
                d[k] = v_d
    # If `symmetric` is enabled, we must process keys which **appear in `d_b` but not in `d_a`**.
    # This is because we already processed all the keys in `d_a` in the loop above.
    if symmetric:
        for k, v_b in d_b.items():
            if k not in d_a:
                v_d = value_op(UNDEFINED, v_b)
                if v_d is not UNDEFINED:
                    d[k] = v_d
    return d


def _merge_value(x, y):
    """Value operator function used in dict merge operations.

    Returns the value in the first dict if the second dict does not define a value for the
    corresponding key, otherwise returns the second value. This corresponds to preserving the
    default value but allowing it to be overridden in the second dictionary.
    """
    return x if y is UNDEFINED else y


def _asymmetric_value_diff(x, y):
    """Value operator function used in asymmetric dict diffs.

    Simply compares the two values with the equality operator, and returns the first value
    (corresponding to the first dict in the diff call) in case they're different.
    """
    return UNDEFINED if x == y else x


def _symmetric_value_diff(x, y):
    """Value operator function used in symmetric dict diffs.

    Simply compares the two values with the equality operator, and returns a tuple containing the
    two values in case they're different.
    """
    return UNDEFINED if x == y else (x, y)
