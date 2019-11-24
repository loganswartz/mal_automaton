#!/usr/bin/env python3

import pytest
import mementos
from mal_automaton.mal import MAL_Series, MAL_Franchise


@pytest.fixture
def BlankMemoCache():
    mementos.core._memento_cache = {}


@pytest.mark.usefixtures('BlankMemoCache')
class TestConstructors:
    """ Tests instantiation of class objects with the given args and kwargs """
    cases = [
        (MAL_Series, [16498], {}),
        (MAL_Series, [], {'name': 'Attack on Titan'}),
        (MAL_Franchise, [16498], {}),
        (MAL_Franchise, [], {'name': 'Attack on Titan'}),
    ]

    @pytest.mark.parametrize(('cls','args','kwargs'), cases, ids=str)
    def test_constructor(self, cls, args, kwargs):
        assert cls(*args, **kwargs)


def test_series_memoization():
    assert MAL_Series(16498) is MAL_Series(name='Attack on Titan')

