#!/usr/bin/env python3

# Imports {{{
# builtins
import sys
import re
import json
import pathlib
import argparse
from datetime import datetime

# 3rd party
from flask import Flask, request
from cheroot.wsgi import Server as WSGIServer, PathInfoDispatcher

# }}}


def parse_for_id(webhook):
    regex = r'thetvdb:\/\/(\d*)'
    result = re.search(regex, webhook['Metadata']['grandparentGuid'])
    return result.group(1)


def create_app(log_location: pathlib.Path):
    app = Flask(__name__)

    @app.route('/', methods=['POST'])
    def record():
        print("Webhook recieved:")
        webhook = json.loads(request.form['payload'])

        timestamp = datetime.now().isoformat()
        show = webhook['Metadata']['grandparentTitle']
        id = parse_for_id(webhook)
        season = webhook['Metadata']['parentIndex']
        episode = webhook['Metadata']['index']
        event = webhook['event'].split('.')[-1]

        print(f"  Event: {event}")
        print(f"  Item: {show}, S{season}E{episode}")

        if not log_location.is_dir():
            log_location.mkdir()

        log = log_location / f"{timestamp}-{show}-{id}-S{season}E{episode}-{event}.json"
        with log.open('w') as fp:
            json.dump(webhook, fp, indent=4)

        return "OK"

    return app


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-o',
        '--output',
        help='Location to save webhooks to',
        type=lambda path: pathlib.Path(path).expanduser().resolve(),
        default='./webhooks',
    )
    parser.add_argument(
        '-m',
        '--netmask',
        help='Netmask for the server to listen on',
        default="127.0.0.1",
    )
    parser.add_argument(
        '-p',
        '--port',
        help='Port to listen on',
        type=int,
        default=8088,
    )
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    app = create_app(args.output)

    d = PathInfoDispatcher({"/": app})
    server = WSGIServer((args.netmask, args.port), d)
    try:
        print(f"Logging location set to: {args.output}")
        print(f"Listening on {args.netmask}:{args.port}....")
        server.start()
    except KeyboardInterrupt:
        print("Exiting....")
        sys.exit(0)


if __name__ == "__main__":
    main()
