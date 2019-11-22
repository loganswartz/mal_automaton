#!/usr/bin/env python3

# builtins
from enum import Enum
import re

# 3rd party
from dateutil.parser import isoparse
from dateutil.tz import UTC

# my modules
from mal_automaton.utils import AttrDict
from mal_automaton.enums import PlexEvent


class PlexWebhook(object):
    def __init__(self, webhook):
        # convert to AttrDict for easier use here
        webhook = AttrDict(webhook)

        self.is_server_hook = webhook.owner
        self.is_user_hook = webhook.user
        # convert to enum
        self.event = PlexEvent(webhook.event)
        # get series, season, and episode data from webhook
        self.media = MediaObject(webhook.Metadata)
        self.user = PlexUser(webhook.Account)
        self.server = PlexServer(webhook.Server)
        self.device = PlexDevice(webhook.Player)


class PlexUser(object):
    def __init__(self, account):
        self.id = account.id
        self.name = account.title


class PlexServer(object):
    def __init__(self, server):
        self.uuid = server.uuid
        self.name = server.title


class PlexDevice(object):
    def __init__(self, player):
        self.uuid = player.uuid
        self.ip = player.publicAddress
        self.name = player.title
        self.local = player.local


class MediaObject(object):
    class LibrarySectionType(Enum):
        Show = 'show'
        Movie = 'movie'
        Music = 'music'

    class MediaType(Enum):
        Episode = 'episode'
        Movie = 'movie'

    def __init__(self, metadata):
        self.library_type = self.LibrarySectionType(metadata.librarySectionType)
        self.library_title = metadata.librarySectionTitle
        self.media_type = self.MediaType(metadata.type)

        if self.media_type is self.MediaType.Episode:
            self.title = metadata.title
            self.series = metadata.grandparentTitle
            self.season = metadata.parentIndex
            self.episode = metadata.index
            self.airdate = isoparse(metadata.originallyAvailableAt).astimezone(UTC)

            # get tvdb_id
            regex = r'com\.plexapp\.agents\.thetvdb:\/\/(\d+)\?'
            match = re.search(regex, metadata.grandparentGuid)
            self.tvdb_id = int(match.group(1)) if match else None

