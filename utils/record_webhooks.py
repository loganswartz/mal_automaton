#!/usr/bin/env python3

# Imports {{{
# builtins
import sys
import json
import pathlib
import argparse

# 3rd party
from flask import Flask
from cheroot.wsgi import Server as WSGIServer, PathInfoDispatcher

# }}}


def create_app(log_location: pathlib.Path):
    app = Flask(__name__)

    @app.route('/')
    def record():
        print("Webhook recieved:")
        webhook = request.get_json(force=True)

        show = webhook['Metadata']['grandparentTitle']
        season = webhook['Metadata']['parentIndex']
        episode = webhook['Metadata']['index']
        event = webhook['event']
        print("  Event: {event}")
        print("  Item: {show}, S{season}E{episode}")

        if not log_location.is_dir():
            log_location.mkdir()

        log = log_location / f"{show}-S{season}E{episode}-{event}.json"
        with log.open('w') as fp:
            json.dump(webhook, fp, indent=4)

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
