#!/usr/bin/env python3

from enum import Enum


class MultiValueEnum(Enum):
    def __new__(cls, *values):
        obj = object.__new__(cls)
        # first value is canonical value
        obj._value_ = values[0]
        for other_value in values[1:]:
            cls._value2member_map_[other_value] = obj
        obj._all_values = values
        return obj

    def __repr__(self):
        return f'<{self.__class__.__name__}.{self._name_}: {", ".join([repr(v) for v in self._all_values])}>'


class WatchStatus(Enum):
    Watching = 1
    Completed = 2
    OnHold = 3
    Dropped = 4
    PlanToWatch = 6


class AnimeType(Enum):
    TV = 'TV'
    Movie = 'Movie'
    OVA = 'OVA'
    ONA = 'ONA'
    Special = 'Special'


class AiringStatus(MultiValueEnum):
    Airing = 'Airing', 1
    Finished = 'Finished Airing', 2
    NotYetAired = 'Not yet aired', 3


class AnimeSource(Enum):
    FourKomaManga = '4-koma manga'
    Game = 'Game'
    LightNovel = 'Light novel'
    Manga = 'Manga'
    Novel = 'Novel'
    Original = 'Original'
    Other = 'Other'
    VisualNovel = 'Visual novel'
    WebManga = 'Web manga'


class PlexEvent(Enum):
    play = 'media.play'
    stop = 'media.stop'
    pause = 'media.pause'
    resume = 'media.resume'
    scrobble = 'media.scrobble'
    rate = 'media.rate'

