#!/usr/bin/env python3

# builtins
import json
from pathlib import Path
import logging

# my modules
from mal_automaton.plex import PlexWebhook
from mal_automaton.translate import tvdb_to_mal


log = logging.getLogger('mal_automaton')


def load_webhook(path):
    return PlexWebhook(json.load(path.open()))


if __name__ == "__main__":
    # load faux payload
    examples = {
        'NoGunsLife': Path('~/examples/plex_webhooks/others/23.json').expanduser(),
        'DrStone': Path('~/examples/plex_webhooks/others/28.json').expanduser(),
        'KonoSuba': Path('~/examples/plex_webhooks/others/33.json').expanduser(),
    }

    webhook_path = examples['KonoSuba']
    # get mal_id from webhook
    webhook = load_webhook(webhook_path)
    mal_id = tvdb_to_mal(webhook)
