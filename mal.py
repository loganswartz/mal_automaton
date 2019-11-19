#!/usr/bin/env python3

# builtins
import pathlib
from difflib import SequenceMatcher
from itertools import combinations
from collections import Counter

# 3rd party
from jikanpy import Jikan
from dateutil.parser import isoparse
from mementos import memento_factory, with_metaclass

# my modules
from mal_automaton.anime import AnimeType


def mal_id_from_info(id=None, *, name=None):
    """
    Function that returns a MAL ID from either a given name or ID. Used by the
    memento factory to allow us to memoize based on the actual MAL ID of a
    series initialized through a name, instead of defaulting to memoizing based
    on init parameters (default mementos behavior)
    """
    jikan = Jikan()
    if id:
        mal_id = id
    elif name:
        mal_id = jikan.search('anime', name)['results'][0]['mal_id']
    else:
        raise ValueError('You must specify an ID or name.')
    return mal_id

def episode_id_from_info(series, data):
    return (series, data['episode_id'])

"""
Create the factories. The lambda function returns a key to be used as the index
whatever we are caching. Since mementos uses one big unified dict as the cache,
we build a tuple containing the class and the key we actually want to use, and
we use that as the key. Without including the class in the tuple, creating a
series with the same ID as an already created Franchise will only return that
franchise, and vice versa.
"""
MAL_SeriesMemoizer = memento_factory('MAL_SeriesMemoizer', lambda cls, args, kwargs: (cls, mal_id_from_info(*args, **kwargs)) )
MAL_EpisodeMemoizer = memento_factory('MAL_EpisodeMemoizer', lambda cls, args, kwargs: (cls, episode_id_from_info(*args, **kwargs)) )


class MAL_Franchise(metaclass=MAL_SeriesMemoizer):
    def __init__(self, id, **kwargs):
        self._jikan = Jikan()
        self.series = self.get_franchise_list(id)
        self.title = self.discern_title()   # assume that the first series is the title of the franchise
        self.release_run = (self.series[0].premiered, self.series[-1].ended)   # TODO: check if show is still airing and change accordingly
        self._absolute = [episode for series in self.series for episode in series.episodes]

    def discern_title(self):
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
            best_match = substrings.most_common(1)[0][0]
        else:
            best_match = None
        # don't return substrings less than 4 characters
        return best_match if best_match is not None and len(best_match) >= 4 else self.series[0].title

    def get_franchise_list(self, mal_id):
        """
        This function takes a MAL anime ID, finds all the sequels and prequels to
        that series, and returns info on them all in an ordered array. Essentially,
        gets all the seasons of a series, since traditionally in America, an anime
        will have several seasons all under one show name, but in Japan, each season
        is its own standalone 'series' that is a sequel to the previous series.
        """
        # fetch info on the provided ID
        original = self._jikan.anime(mal_id)

        # create deep copy of object
        current = original.copy()

        # storing the actual objects vs just the id's
        # anime_list = [original]
        anime_list = [current['mal_id']]

        # get all prequels and prepend to list
        while 'Prequel' in current['related']:
            # prepend prequel to list
            prequel = self._jikan.anime(current['related']['Prequel'][0]['mal_id'])
            # storing the actual objects vs just the id's
            # anime_list = [prequel] + anime_list
            anime_list = [prequel['mal_id']] + anime_list
            # set current to prequel, and repeat until we reach the first season
            current = prequel

        # reset current
        current = original.copy()

        # get all sequels and append to list
        while 'Sequel' in current['related']:
            # append sequel to list
            sequel = self._jikan.anime(current['related']['Sequel'][0]['mal_id'])
            # storing the actual objects vs just the id's
            # anime_list = anime_list + [sequel]
            anime_list = anime_list + [sequel['mal_id']]
            # set current to sequel, and repeat until we reach the last season
            current = sequel

        # return finished list
        return [MAL_Series(i) for i in anime_list]

    def absolute_episode(self, index):
        # make one big (ordered) list of episodes, and get the correct index from that list
        return self._absolute[index-1]

    def __repr__(self):
        return f"<MAL_Franchise: {self.title}>"


class MAL_Series(metaclass=MAL_SeriesMemoizer):
    def __init__(self, mal_id, **kwargs):
        self._jikan = Jikan()
        self._raw = self._jikan.anime(mal_id)
        # MAL meta info
        self.id = mal_id
        self.url = self._raw['url']
        self.image_url = self._raw['image_url']
        # titles
        self.title = self._raw['title']
        self.title_en = self._raw['title_english']
        self.title_jp = self._raw['title_japanese']
        self.synonyms = self._raw['title_synonyms']
        # series meta info
        self.type = AnimeType(self._raw['type'])
        self.source = self._raw['source']   # TODO: source material enum
        self.status = self._raw['status']   # TODO: airing status enum
        self.score = self._raw['score']
        self.rank = self._raw['rank']
        # release date info
        self.airing = self._raw['airing']   # bool
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
            for i in range(2, last_page+1):
                episodes += self._jikan.anime(self.id, extension='episodes', page=i)['episodes']
        # return as episode object
        return [MAL_Episode(self, ep) for ep in episodes]

    def __repr__(self):
        return f"<MAL_Series: {self.title} [{self.id}]>"


class MAL_Episode(metaclass=MAL_EpisodeMemoizer):
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
        return f"<MAL_Episode: {self.title} [{self.id}]>"

