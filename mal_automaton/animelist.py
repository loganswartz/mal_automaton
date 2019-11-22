#!/usr/bin/env python3

# builtins
import logging

# 3rd party
from jikanpy import Jikan
# from jikanpy.exceptions import APIException

# my modules
from mal_automaton.mal import MAL_Series
from mal_automaton.enums import AnimeType, AiringStatus, WatchStatus


log = logging.getLogger(__name__)


class AnimeList(object):
    def __init__(self, username):
        self.user = username
        self._api = Jikan()
        self.update()

    def update(self):
        _list = self._api.user(username=self.user, request='animelist')['anime']
        self._list = [AnimeListEntry(i) for i in _list]

    def __len__(self):
        return len(self._list)

    def __iter__(self):
        self._iter = 0
        return self

    def __next__(self):
        if self._iter < len(self._list):
            self._iter += 1
            return self._list[self._iter - 1]
        else:
            raise StopIteration

    def __repr__(self):
        return f'<AnimeList: {self.user} [{len(self)}]>'

    def __contains__(self, obj):
        return obj in self._list

    def __getitem__(self, index):
        return self._list[index]

    @property
    def PTW(self):
        return [i for i in self._list if i.status.watching is WatchStatus.PlanToWatch]

    @property
    def Watching(self):
        return [i for i in self._list if i.status.watching is WatchStatus.Watching]

    @property
    def Completed(self):
        return [i for i in self._list if i.status.watching is WatchStatus.Completed]


class AnimeListEntry(object):
    def __init__(self, data):
        self.id = data['mal_id']
        self.title = data['title']
        self.type = AnimeType(data['type'])
        self.airing = AiringStatus(data['airing_status'])
        self.total_episodes = data['total_episodes']
        self._series = None

        # user specific
        args = {
            'status': data['watching_status'],
            'score': data['score'],
            'watched_episodes': data['watched_episodes'],
        }
        self.status = AnimeStatus(**args)

    @property
    def series(self):
        if not self._series:
            self._series = MAL_Series(self.id)
        return self._series

    def __repr__(self):
        return f"<AnimeListEntry: {self.title} [{self.id}]>"

    def __eq__(self, other):
        return self.series is other.series


class AnimeStatus(object):
    def __init__(self, *, status, score, watched_episodes):
        self.watching = WatchStatus(status)
        self.score = score
        self.watched_episodes = watched_episodes

