#!/usr/bin/env python3

# builtins
import pathlib
from difflib import SequenceMatcher
from itertools import combinations
from collections import Counter

# 3rd party
from jikanpy import Jikan
from dateutil.parser import isoparse

# my modules
from mal_automaton.anime import AnimeType


class MAL_Franchise(object):
    def __init__(self, mal_id):
        self._jikan = Jikan()
        self.series = self.get_franchise_list(mal_id)
        self.title = self.discern_title()   # assume that the first series is the title of the franchise
        self.release_run = (self.series[0].premiered, self.series[-1].ended)   # TODO: check if show is still airing and change accordingly

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

    def __repr__(self):
        return f"<MAL_Franchise: {self.title}>"


class MAL_Series(object):
    def __init__(self, mal_id):
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
        self.sequel = self._raw['related'].get('Sequel')
        self.prequel = self._raw['related'].get('Prequel')

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
        return [MAL_Episode(ep) for ep in episodes]

    def __repr__(self):
        return f"<MAL_Series: {self.title} [{self.id}]>"


class MAL_Episode(object):
    def __init__(self, data):
        self.id = data['episode_id']
        self.title = data['title']
        self.title_romanji = data['title_romanji']
        self.airdate = data['aired']
        self.is_filler = data['filler']
        self.is_recap = data['recap']
        self.video_url = data['video_url']

    def __repr__(self):
        return f"<MAL_Episode: {self.title} [{self.id}]>"

