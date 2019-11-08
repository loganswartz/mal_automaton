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

def get_mal_franchise(series_name):
    mal = Jikan()

    # get the top / first result for the series title
    results = mal.search('anime', series_name, parameters={'limit': 1})

    # extract MAL id
    mal_id = results['results'][0]['mal_id']
    log.debug(f"MAL returned {mal_id} as the most likely match for the title '{series_name}'.")

    # get all prequels and sequels (seasons)
    franchise = get_all_seasons(mal_id)
    log.debug(f"Fetched franchise: {list(map(lambda i: i['title'], franchise))}")

    # return list of series (in canonical series order)
    return franchise


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

def get_all_seasons(mal_id):
    """
    This function takes a MAL anime ID, finds all the sequels and prequels to
    that series, and returns info on them all in an ordered array. Essentially,
    gets all the seasons of a series, since traditionally in America, an anime
    will have several seasons all under one show name, but in Japan, each season
    is its own standalone 'series' that is a sequel to the previous series.
    """
    mal = Jikan()

    # fetch info on the provided ID
    original = mal.anime(mal_id)

    # create deep copy of object
    current = original.copy()
    anime_list = [original]

    # get all prequels and prepend to list
    while 'Prequel' in current['related']:
        # prepend prequel to list
        prequel = mal.anime(current['related']['Prequel'][0]['mal_id'])
        anime_list = [prequel] + anime_list
        # set current to prequel, and repeat until we reach the first season
        current = prequel

    # reset current
    current = original.copy()

    # get all sequels and append to list
    while 'Sequel' in current['related']:
        # append sequel to list
        sequel = mal.anime(current['related']['Sequel'][0]['mal_id'])
        anime_list = anime_list + [sequel]
        # set current to sequel, and repeat until we reach the last season
        current = sequel

    # return finished list
    return anime_list


def get_all_mal_episodes(mal_id):
    """
    Essentially just a function to fetch and de-paginate the results of an
    episode search via Jikan
    """
    mal = Jikan()

    data = mal.anime(mal_id, extension='episodes')
    episodes = data['episodes']
    last_page = data['episodes_last_page']
    if last_page > 1:
        for i in range(2, last_page+1):
            episodes += mal.anime(mal_id, extension='episodes', page=i)['episodes']
    return episodes

