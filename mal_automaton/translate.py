#!/usr/bin/env python3

# builtins
import logging
from datetime import timedelta

# my modules
from mal_automaton.utils import pretty_print
from mal_automaton.mal import MAL_Franchise


log = logging.getLogger(__name__)


def one_day_apart(airdate, episode):
    """Compares 2 dates, returns if the difference < 1 day"""
    delta = timedelta(days=1, seconds=1)
    if not airdate or not episode.airdate:   # if airdate in MAL is null, abort
        return False
    log.debug(f"{episode.title} - mal: {episode.airdate}; tvdb: {airdate}")
    return abs(episode.airdate - airdate) < delta


def tvdb_to_mal(webhook):
    """
    Takes a raw webhook sent from plex, and finds the MAL ID's for the episode
    specified in the webhook. Plex references everything by TVDB identifiers,
    so we essentially scrape for some identifying information from TVDB and use
    that to match to an episode in MAL.
    """

    # try to get franchise based on tvdb show title
    franchise = MAL_Franchise(name=webhook.media.series)

    # check all seasons for the given episode
    log.info(f"Episode to find is '{webhook.media.title}'.")
    for series in franchise.series:
        log.info(f"Checking {series.title}....")

        # get all episodes for the series
        log.debug('Episodes:')
        pretty_print(series.episodes, debug=True)

        filtered = [ep for ep in series.episodes if one_day_apart(webhook.media.airdate, ep)]

        # log.debug(f'Filtered:')
        # pretty_print(filtered, debug=True)
        if filtered:
            log.info(f"MAL Series is {series}")
            log.info(f"MAL Episode is {filtered[0]}")
            return {'mal_id': series.id, 'episode': filtered[0].id}

        log.info('No episode found by airdate, trying by name....')
        filtered = [ep for ep in series.episodes if webhook.media.title == ep.title]

        if filtered:
            log.info(f"MAL Series is {series}")
            log.info(f"MAL Episode is {filtered[0]}")
            return {'mal_id': series.id, 'episode': filtered[0].id}

    return False


def get_absolute_episode(index: int, ep_list: list):
    filtered = list(filter(lambda ep: ep['absoluteNumber'] == index, ep_list))
    if len(filtered) > 1:
        raise ValueError('More than 1 episode found with an absolute index of {index}.')
    return filtered[0]

