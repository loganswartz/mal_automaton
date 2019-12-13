#!/usr/bin/env python3

# builtins
from difflib import SequenceMatcher
from itertools import combinations
from collections import Counter
from textwrap import shorten

# 3rd party
from jikanpy import Jikan
from dateutil.parser import isoparse

# my modules
from mal_automaton.memoizer import memento_factory
from mal_automaton.enums import AnimeType, AiringStatus, AnimeSource


def SeriesIDFactory(cls, *args, **kwargs):
    """
    Function that returns a MAL ID from either a given name or ID. Used by the
    memento factory to allow us to memoize based on the actual MAL ID of a
    series initialized through a name, instead of defaulting to memoizing based
    on init parameters (default mementos behavior)
    """
    def series_memo_identifier(id=None, *, name=None):
        jikan = Jikan()
        if id:
            mal_id = id
        elif name:
            mal_id = jikan.search('anime', name)['results'][0]['mal_id']
        else:
            raise ValueError('You must specify an ID or name.')
        return mal_id

    return series_memo_identifier(*args, **kwargs)


def EpisodeIDFactory(cls, *args, **kwargs):
    def episode_memo_identifier(series, data):
        return (series, data['episode_id'])

    return episode_memo_identifier(*args, **kwargs)


"""
Create the factory. The factory calls a function that returns a key to be used
as the index whatever we are caching. Since mementos uses one big unified dict
as the cache, we build a tuple containing the class and the key we actually want
to use, and we use that as the key. Without including the class in the tuple,
creating a series with the same ID as an already created Franchise will only
return that franchise, and vice versa.
"""
MAL_SeriesMemoizer = memento_factory('MAL_SeriesMemoizer', SeriesIDFactory, use_key=True)
MAL_EpisodeMemoizer = memento_factory('MAL_EpisodeMemoizer', EpisodeIDFactory)


class MAL_Franchise(object, metaclass=MAL_SeriesMemoizer):
    def __init__(self, id=None, *, name=None):
        self._jikan = Jikan()
        self.series = self._get_franchise_list(id)
        self.title = self._discern_title()
        self.release_run = (self.series[0].premiered, self.series[-1].ended)
        self._absolute = [ep for series in self.series for ep in series.episodes]

    def _discern_title(self):
        substrings = Counter()

        # compare all combinations of series titles in the franchise
        combos = combinations(self.series, 2)
        for (a, b) in combos:
            matcher = SequenceMatcher(None, a.title, b.title)
            diff = matcher.find_longest_match(0, len(a.title), 0, len(b.title))
            if diff:
                string = a.title[diff.a:diff.size]
                substrings[string] += 1

        # check if we got any matches
        if substrings.most_common(1):
            best = substrings.most_common(1)[0][0]
        else:
            best = None
        # don't return substrings less than 4 characters
        return best if best is not None and len(best) >= 4 else self.series[0].title

    def _get_franchise_list(self, id):
        """
        This function takes a MAL anime ID, finds all the sequels and prequels to
        that series, and returns info on them all in an ordered array. Essentially,
        gets all the seasons of a series, since traditionally in America, an anime
        will have several seasons all under one show name, but in Japan, each season
        is its own standalone 'series' that is a sequel to the previous series.
        """
        # fetch info on the provided ID
        original = MAL_Series(id)

        current = original
        anime_list = [current]

        # get all prequels and prepend to list
        while current.prequel:
            # prepend prequel to list
            anime_list = [current.prequel] + anime_list
            # set current to prequel, and repeat until we reach the first season
            current = current.prequel

        # reset current
        current = original

        # get all sequels and append to list
        while current.sequel:
            # append sequel to list
            anime_list = anime_list + [current.sequel]
            # set current to sequel, and repeat until we reach the last season
            current = current.sequel

        # return finished list
        return anime_list

    def absolute_episode(self, index):
        # make one big (ordered) list of episodes, and get the correct index from that list
        return self._absolute[index - 1]

    def __repr__(self):
        return f"<MAL_Franchise: {self.title}>"


class MAL_Series(object, metaclass=MAL_SeriesMemoizer):
    def __init__(self, id=None, *, name=None):
        self._jikan = Jikan()
        self.id = id
        self._raw = self._jikan.anime(self.id)
        self._cached = self._raw['request_cached']
        # MAL meta info
        self.url = self._raw['url']
        self.image_url = self._raw['image_url']
        # titles
        self.title = self._raw['title']
        self.title_en = self._raw['title_english']
        self.title_jp = self._raw['title_japanese']
        self.synonyms = self._raw['title_synonyms']
        # series meta info
        self.type = AnimeType(self._raw['type'])
        self.source = AnimeSource(self._raw['source'])
        self.status = AiringStatus(self._raw['status'])
        self.score = self._raw['score']
        self.rank = self._raw['rank']
        # release date info
        self.airing = self._raw['airing']   # bool
        if not self._raw['aired']['from']:
            self.premiered = None
        else:
            self.premiered = isoparse(self._raw['aired']['from'])
        if not self._raw['aired']['to']:
            self.ended = None
        else:
            self.ended = isoparse(self._raw['aired']['to'])
        self.release_run = self._raw['aired']['string']
        self.release_season = self._raw['premiered']
        # series info
        self.synopsis = self._raw['synopsis']
        self.background = self._raw['background']
        self.studio = self._raw['studios']
        self.rating = self._raw['rating']
        self.episodes = self.fetch_episodes()
        try:
            self._sequel_id = self._raw['related'].get('Sequel')[0]['mal_id']
        except TypeError:
            self._sequel_id = None
        try:
            self._prequel_id = self._raw['related'].get('Prequel')[0]['mal_id']
        except TypeError:
            self._prequel_id = None

    @property
    def sequel(self):
        return MAL_Series(self._sequel_id) if self._sequel_id else None

    @property
    def prequel(self):
        return MAL_Series(self._prequel_id) if self._prequel_id else None

    def fetch_episodes(self):
        """
        Fetch all episodes of a series (automatically de-paginates, so we
        *actually* get them all, not just the first page)
        """
        resp = self._jikan.anime(self.id, extension='episodes')
        episodes = resp['episodes']
        last_page = resp['episodes_last_page']
        if last_page > 1:
            for i in range(2, last_page + 1):
                episodes += self._jikan.anime(self.id, extension='episodes', page=i)['episodes']
        # return as episode object
        return [MAL_Episode(self, ep) for ep in episodes]

    def __repr__(self):
        return f"<MAL_Series: {self.title} [{self.id}]>"


class MAL_Episode(object, metaclass=MAL_EpisodeMemoizer):
    def __init__(self, series, data):
        self.series = series
        self.id = data['episode_id']
        self.title = data['title']
        self.title_romanji = data['title_romanji']
        self.airdate = isoparse(data['aired']) if data['aired'] else None
        self.is_filler = data['filler']
        self.is_recap = data['recap']
        self.video_url = data['video_url']

    def __repr__(self):
        short_title = shorten(self.series.title, width=20, placeholder='...')
        return f"<MAL_Episode: {short_title} - '{self.title}' [E{self.id:02}]>"

