#!/usr/bin/env python3

# builtins
from itertools import groupby

# 3rd party
import tvdbsimple as tvdb
from dateutil.parser import isoparse
from dateutil.tz import UTC

# my modules
from mal_automaton.memoizer import memento_factory


def TVDB_SeriesIDFactory(cls, *args, **kwargs):
    """
    Function that returns a TVDB ID from either a given name or ID. Used by the
    memento factory to allow us to memoize based on the actual TVDB ID of a
    series initialized through a name, instead of defaulting to memoizing based
    on init parameters (default mementos behavior)
    """
    def series_memo_identifier(id=None, *, name=None):
        search = tvdb.Search()
        if id:
            tvdb_id = id
        elif name:
            tvdb_id = search.series(name)[0]['id']
        else:
            raise ValueError('You must specify an ID or name.')
        return tvdb_id

    return series_memo_identifier(*args, **kwargs)


def TVDB_SeasonIDFactory(cls, *args, **kwargs):
    def season_memo_identifier(series, number, episodes):
        return (series, number)

    return season_memo_identifier(*args, **kwargs)


def TVDB_EpisodeIDFactory(cls, *args, **kwargs):
    def episode_memo_identifier(series, season, id):
        return (series, season, id)

    return episode_memo_identifier(*args, **kwargs)


TVDB_SeriesMemoizer = memento_factory('TVDB_SeriesMemoizer', TVDB_SeriesIDFactory, use_key=True)
TVDB_SeasonMemoizer = memento_factory('TVDB_SeasonMemoizer', TVDB_SeasonIDFactory)
TVDB_EpisodeMemoizer = memento_factory('TVDB_EpisodeMemoizer', TVDB_EpisodeIDFactory)


class TVDB_Series(object, metaclass=TVDB_SeriesMemoizer):
    def __init__(self, id=None, *, name=None):
        self.id = id
        self._raw = tvdb.Series(self.id)
        self._raw.info()
        self.series_id = self._raw.seriesId
        self.title = self._raw.seriesName
        self.language = self._raw.language   # TODO: enum
        self.aliases = self._raw.aliases
        self.status = self._raw.status   # TODO: enum
        self.rating = self._raw.rating   # TODO: enum
        self.network = self._raw.network
        self.runtime = self._raw.runtime
        self.airtime = self._raw.airsTime
        self.airday = self._raw.airsDayOfWeek
        self.genres = self._raw.genre   # TODO: enum
        self.overview = self._raw.overview
        self.imdb_id = self._raw.imdbId
        self.zap2it_id = self._raw.zap2itId
        self.slug = self._raw.slug
        self._seasons = None

    @property
    def seasons(self):
        if self._seasons:
            return self._seasons

        self._raw.Episodes.all()
        _episodes = sorted(self._raw.Episodes.episodes, key=lambda ep: ep['airedSeason'])
        _seasons = {key: list(group) for key, group in groupby(_episodes, lambda ep: ep['airedSeason'])}
        # convert to Season objects
        self._seasons = {num: TVDB_Season(self, num, eps) for num, eps in _seasons.items()}
        return self._seasons

    @property
    def specials(self):
        return self.seasons[0]

    def __repr__(self):
        return f"<TVDB_Series: {self.title}>"


class TVDB_Season(object, metaclass=TVDB_SeasonMemoizer):
    def __init__(self, series, number, episodes):
        self.series = series
        self.number = number
        self.episodes = {}
        for ep in episodes:
            self.episodes[ep['airedEpisodeNumber']] = TVDB_Episode(self.series, self, ep['id'])

    def __repr__(self):
        return f"<TVDB_Season: {self.series.title} S{self.number:02}>"


class TVDB_Episode(object, metaclass=TVDB_EpisodeMemoizer):
    def __init__(self, series, season, id):
        self.id = id
        self.series = series
        self.season = season
        self._raw = tvdb.Episode(id)
        self._raw.info()

        self.number = self._raw.airedEpisodeNumber
        self.absolute = self._raw.absoluteNumber
        self.title = self._raw.episodeName
        self.airdate = isoparse(self._raw.firstAired).astimezone(UTC)
        self.rating = self._raw.contentRating   # TODO: enum
        self.overview = self._raw.overview
        self.directors = self._raw.directors

    def __repr__(self):
        return f"<TVDB_Episode: {self.series.title} S{self.season.number:02}E{self.number:02}>"

