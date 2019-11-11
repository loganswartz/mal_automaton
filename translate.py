#!/usr/bin/env python3

# builtins
import pathlib
import json
import pathlib
import logging
import sys
import re

# 3rd party
import requests
from jikanpy import Jikan
import tvdbsimple as tvdb
from datetime import timedelta
from dateutil.parser import isoparse
from dateutil.tz import UTC

# my modules
from mal_automaton.account import MAL_Account
from mal_automaton.utils import pretty_print


log = logging.getLogger(__name__)


def tvdb_to_mal(webhook):
    """
    Takes a raw webhook sent from plex, and finds the MAL ID's for the episode
    specified in the webhook. Plex references everything by TVDB identifiers,
    so we essentially scrape for some identifying information from TVDB and use
    that to match to an episode in MAL.
    """

    # try to get franchise based on tvdb show title
    franchise = get_mal_franchise(webhook.media.series)

    # check all seasons for the given episode
    log.info(f"Episode to find is '{webhook.media.title}'.")
    for series in franchise:
        log.info(f"Checking {series['title']}....")

        # get all episodes for the series
        episodes = get_all_mal_episodes(series['mal_id'])
        log.debug('Episodes:')
        pretty_print(episodes, debug=True)

        filtered = find_equivalent_by_date(webhook.media.airdate, episodes)

        # log.debug(f'Filtered:')
        # pretty_print(filtered, debug=True)
        if filtered:
            log.info(f"MAL ID is {series['mal_id']}")
            return {'mal_id': series['mal_id'], 'episode': filtered[0]['episode_id']}

        log.info('No episode found by airdate, trying by name....')
        filtered = list(filter(lambda ep: ep['title'] == webhook.media.title, episodes))

        if filtered:
            log.info(f"MAL ID is {series['mal_id']}")
            return {'mal_id': series['mal_id'], 'episode': filtered[0]['episode_id']}

    return False


def find_equivalent_by_date(airdate, episode_list):
        def one_day_apart(episode):
            """Compares 2 dates, returns if the difference < 1 day"""
            delta = timedelta(days=1, seconds=1)
            if not episode['aired']:   # if airdate in MAL is null, abort
                return False
            mal_airdate = isoparse(episode['aired'])
            log.debug(f"{episode['title']} - mal: {mal_airdate}; tvdb: {airdate}")
            return abs(mal_airdate-airdate) < delta

        # check if played episode is in the MAL series using airdates
        return list(filter(one_day_apart, episode_list))


def get_absolute_episode(index: int, ep_list: list):
    filtered = list(filter(lambda ep: ep['absoluteNumber'] == index, ep_list))
    if len(filtered) > 1:
        raise ValueError('More than 1 episode found with an absolute index of {index}.')
    return filtered[0]

