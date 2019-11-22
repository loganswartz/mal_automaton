#!/usr/bin/env python3

from mal_automaton.mal import MAL_Series


def test_series_memoization():
    assert MAL_Series(16498) is MAL_Series(name='Attack on Titan')

