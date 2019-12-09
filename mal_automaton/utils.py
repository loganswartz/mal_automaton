#!/usr/bin/env python3

# buitlins
import logging


log = logging.getLogger(__name__)


def retry(tries=1):
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
        string += f' > "{i.title}"\n'
    string += '# -----------------------------------\n'
    if debug:
        log.debug('\n' + string)
    else:
        print(string)

