#!/usr/bin/env python3

# builtins
from enum import Enum
import logging

# 3rd party
from jikanpy import Jikan
#from jikanpy.exceptions import APIException

# my modules
from mal_automaton.utils import AttrDict


log = logging.getLogger(__name__)

class AnimeList(object):
    def __init__(self, username):
        self.username = username
        self._api = Jikan()
        self.update()

    def update(self):
        _list = [AttrDict(i) for i in self._api.user(username=self.username, request='animelist')['anime']]
        self.entries = {i.mal_id: AnimeListEntry(i) for i in _list}


class AnimeListEntry(object):
    def __init__(self, data):
        self.id = data.mal_id
        self.title = data.title
        self.url = data.url
        self.type = AnimeType(data.type)
        self.airing = data.airing_status   # TODO: an enum
        self.total_episodes = data.total_episodes

        # user specific
        args = {
            'status': data.watching_status,
            'score': data.score,
            'watched_episodes': data.watched_episodes,
        }
        self.status = AnimeStatus(**args)

class AnimeStatus(object):
    def __init__(self, *, status, score, watched_episodes):
        self.watching = WatchStatus(status)
        self.score = score
        self.watched_episodes = watched_episodes

class WatchStatus(Enum):
    Watching    = 1
    Completed   = 2
    OnHold      = 3
    Dropped     = 4
    PlanToWatch = 6

class AnimeType(Enum):
    TV = 'TV'
    Movie = 'Movie'
    OVA = 'OVA'
    Special = 'Special'

