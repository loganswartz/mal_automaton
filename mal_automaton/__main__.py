#!/usr/bin/env python3

# builtins
import json
from pathlib import Path
import logging
import sys

# my modules
from mal_automaton.plex import PlexWebhook
from mal_automaton.translate import tvdb_to_mal


log = logging.getLogger('mal_automaton')


def load_webhook(path):
    return PlexWebhook(json.load(path.expanduser().open()))


if __name__ == "__main__":
    # try to run for all files passed in as arguments
    if len(sys.argv) <= 1:
        log.info("No webhooks given!")
    else:
        try:
            for file in sys.argv[1:]:
                webhook_path = Path(file).expanduser()

                # load saved webhook and attempt to discern MAL id from the webhook
                webhook = load_webhook(webhook_path)
                results = tvdb_to_mal(webhook)
                if results:
                    log.info(f"MAL ID was determined to be: {results['mal_id']}")
                else:
                    log.info("No MAL equivalent found")
        except Exception:
            log.exception("Exception occurred.")

