#!/usr/bin/env python3

import pytest
import mal_automaton.memoizer
from mal_automaton.tvdb import TVDB_Series


@pytest.fixture
def BlankMemoCache():
    mal_automaton.memoizer._memento_cache = {}


@pytest.mark.usefixtures('BlankMemoCache')
class TestConstructors:
    """ Tests instantiation of class objects with the given args and kwargs """
    cases = [
        (TVDB_Series, [267440], {}),
        (TVDB_Series, [], {'name': 'Attack on Titan'}),
    ]

    @pytest.mark.parametrize(('cls', 'args', 'kwargs'), cases, ids=str)
    def test_constructor(self, cls, args, kwargs):
        assert cls(*args, **kwargs)

# currently doesn't work due to lackluster search matching on TheTVDB's part
# def test_series_memoization():
#     assert TVDB_Series(267440) is TVDB_Series(name='Attack on Titan')

