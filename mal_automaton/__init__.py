#!/usr/bin/env python3

# builtins
import logging
import sys
from pathlib import Path

# 3rd party
import tvdbsimple as tvdb
from yaml import load
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

conf    = Path('~/.mal_automaton.conf')
logfile = Path('~/mal_automaton.log')

# load the config
config = load(conf.expanduser().open(), Loader=Loader)
tvdb.KEYS.API_KEY = config.get('tvdb_api_key')

levels = {
    'DEBUG'   : logging.DEBUG,
    'INFO'    : logging.INFO,
    'WARNING' : logging.WARNING,
    'ERROR'   : logging.ERROR,
    'CRITICAL': logging.CRITICAL
}
loglevel = levels[config.get('loglevel')] if config.get('loglevel') else None


# logging
log = logging.getLogger('mal_automaton')
log.setLevel(loglevel or logging.INFO)   # overall min log level for application
# log debug and above messages to file
debug_format = logging.Formatter('%(name)s: %(levelname)s - %(message)s')
file_log = logging.FileHandler(filename=logfile.expanduser(), mode='w')
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

