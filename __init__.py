#!/usr/bin/env python3

# builtins
import logging
import sys
import json
from pathlib import Path

# 3rd party
import tvdbsimple as tvdb

config = json.load(Path('~/.mal_automaton.conf').expanduser().open())
tvdb.KEYS.API_KEY = config['tvdb_api_key']

# logging
log = logging.getLogger('mal_automaton')
log.setLevel(logging.DEBUG)   # overall min log level for application
# log debug and above messages to file
debug_format = logging.Formatter('%(name)s: %(levelname)s - %(message)s')
file_log = logging.FileHandler(filename='mal_automaton.log', mode='w')
file_log.setLevel(logging.DEBUG)
file_log.setFormatter(debug_format)
# log info and above to stdout
info_format = logging.Formatter('%(name)s: %(message)s')
stdout = logging.StreamHandler(sys.stdout)
stdout.setLevel(logging.INFO)
stdout.setFormatter(info_format)
# enable loggers
log.addHandler(file_log)
log.addHandler(stdout)

