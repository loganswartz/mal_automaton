#!/usr/bin/env python3

# builtins
import pathlib
import json
import sys
import secrets
import string
from datetime import datetime
import time

# 3rd party
import requests
from dateutil.parser import isoparse


class Randomizer(object):
    def __init__(self):
        dictionary_url = "http://svnweb.freebsd.org/csrg/share/dict/words?view=co&content-type=text/plain"
        words = requests.get(dictionary_url).text.splitlines()
        self.wordlist = [i for i in words if not (i[0].isupper() and i[1:].islower())]
        self.namelist = [i for i in words if i[0].isupper() and i[1:].islower()]

    def word(self, num=1):
        return '-'.join([self.wordlist[secrets.choice(range(0, len(self.wordlist)))] for _ in range(num)])

    def name(self, num=1):
        return '-'.join([self.namelist[secrets.choice(range(0, len(self.namelist)))] for _ in range(num)])

    def uuid(self, length):
        return ''.join([secrets.choice(string.ascii_letters[:26] + string.digits) for _ in range(length)])

    def ip(self):
        return '.'.join([str(secrets.choice(range(1, 254))) for _ in range(4)])

    def time(self):
        return str(int(time.time() - secrets.choice(range(31536000))))

    def choice(self, iterable):
        return secrets.choice(iterable)

def sanitize(file):
    rand = Randomizer()

    print(f"Sanitizing {file}....")
    webhook = json.load(file.open())

    webhook['owner'] = rand.choice([True, False])
    webhook['Account']['id'] = rand.choice(range(0, 100))
    webhook['Account']['thumb'] = f"https://plex.tv/users/{rand.uuid(16)}/avatar?c={rand.time()}"
    webhook['Account']['title'] = rand.word(2)
    webhook['Server']['title'] = f"{rand.name()}-plex-server"
    webhook['Server']['uuid'] = rand.uuid(40)
    webhook['Player']['local'] = rand.choice([True, False])
    webhook['Player']['title'] = f"{rand.name()}-pc"
    webhook['Player']['publicAddress'] = rand.ip()
    webhook['Player']['uuid'] = rand.uuid(24)

    # in posix timestamp format
    airdate = int(isoparse(webhook['Metadata'].get('originallyAvailableAt', '2000-01-01')).timestamp())
    now = int(time.time())
    webhook['Metadata']['lastViewedAt'] = rand.choice(range(airdate, now))
    webhook['Metadata']['addedAt'] = rand.choice(range(airdate, now))
    webhook['Metadata']['updatedAt'] = rand.choice(range(airdate, now))

    return webhook


if __name__ == "__main__":

    for arg in sys.argv[1:]:
        path = pathlib.Path(arg).expanduser()

        # directory of files
        if path.is_dir():
            new_dir = path.with_name(path.name + '-sanitized')
            new_dir.mkdir()

            for f in path.iterdir():
                webhook = sanitize(f)
                json.dump(webhook, (new_dir / f.name).open('w+'), indent=4)
            print(f"Sanitized webhooks saved to '{str(new_dir)}'.")
        # just a single file
        else:
            webhook = sanitize(path)
            sanitized = path.with_name(path.stem + '-sanitized' + "".join(path.suffixes))
            json.dump(webhook, sanitized.open('w+'), indent=4)
            print(f"Sanitized webhook saved as '{sanitized.name}'.")

    print('Done.')

