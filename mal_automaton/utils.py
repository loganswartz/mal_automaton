#!/usr/bin/env python3

# buitlins
import logging


log = logging.getLogger(__name__)


def retry(tries = 1):
    """
    Decorator to retry something a certain amount of times. A function using
    this decorator should signal failure via an exception. The resulting
    exception will be raised upon failure of the final try.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            counter = 0
            while counter < tries:
                try:
                    return func(*args, **kwargs)
                except Exception:
                    counter += 1
                    if counter >= counter:
                        raise
        return wrapper
    return decorator


class AttrDict(object):
    """
    This class simply converts a dict to an equivalent object that uses dot
    attribute notation instead of dictionary notation (object.attribute instead
    of object['attribute']). Only converts dicts, and will recurse down to
    nested dicts and convert them too (and also skip down past lists).
    """
    def __init__(self, _dict):
        for key, value in _dict.items():
            if isinstance(value, dict):
                self.__dict__.update({key: AttrDict(value)})
            elif isinstance(value, list):
                # to continue recursing past lists
                self.__dict__.update({key: [AttrDict(i) for i in value]})
            else:
                self.__dict__.update({key: value})


class GenericObject(object):
    """ Simple object that takes any kwargs and adds them as attributes. """
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self.__dict__[key] = value


def pretty_print(list, *, debug=False):
    string = ''
    string += '# -----------------------------------\n'
    for i in list:
        string += f" > '{i.title}'\n"
    string += '# -----------------------------------\n'
    if debug:
        log.debug('\n' + string)
    else:
        print(string)


def get_subarray(arr, key, func = None):
    """
    This function is for when you have an array of dictionaries, and you want
    to find the dictionary containing some subvalue. For example, say you have
    this array:

        array = [
            {'name' = 'a', 'order': 1},   # index = 0
            {'name' = 'b', 'order': 2},   # index = 1
            {'name' = 'c', 'order': 3},   # index = 2
            {'name' = 'd', 'order': 4},   # index = 3
        ]

    You want to find the array with an 'order' value of 3, so you run it through
    this function (Ex: `new = get_subarray(array, 'order')` ), and you will get
    out an array like so:

        new = [
            {1: 0},   # these are {<value of order>, <index in original list>}
            {2: 1},
            {3: 2},
            {4: 3},
        ]

    Thus, you can then check if the subvalue you were looking for exists in one
    of the dictionaries (with `<subvalue you wanted> in new`), and then find the
    original dictionary that value came from with `new[<subvalue you wanted>]`
    """
    # func is an optional function to apply to the keys of the new array
    new = {}
    for index, value in enumerate(arr):
        if func:
            new[func(value[key])] = index
        else:
            new[value[key]] = index
    return new

