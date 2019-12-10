#!/usr/bin/env python3

"""
This code is a tweaked version of the 'mementos' package by Jonathan Eunice,
found here: https://bitbucket.org/jeunice/mementos/src/default/
"""

_memento_cache = {}


def memento_factory(name, func, *, use_key=False):
    """
    Return a memoizing metaclass with the given name and key function.
    That makes this a parametrized meta-metaclass, which is probably
    the most meta thing you've ever seen. If it isn't, both congratulations
    and sympathies are in order!
    """
    def call(cls, *args, **kwargs):
        identifier = func(cls, *args, **kwargs)
        key = (cls, identifier)
        try:
            return _memento_cache[key]
        except KeyError:
            if use_key:
                instance = type.__call__(cls, identifier)
            else:
                instance = type.__call__(cls, *args, **kwargs)
            _memento_cache[key] = instance
            return instance

    mc = type(name, (type,), {'__call__': call})
    return mc


"""
The key differences between this memento_factory() and the one from the
"mementos" package are:
    * The class being memoized is automatically included in the memo cache key,
    instead of needing to be including explicitly.
    * You can choose whether to initialize the object with just the memo cache
    key, or with all the arguments the class was originally called with.
"""

