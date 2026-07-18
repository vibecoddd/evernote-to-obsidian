"""Loopback-only entry point for the Electron Python sidecar."""

import argparse
import os

from web_app import WebMigrator


def run_backend(port: int, debug: bool = False) -> None:
    """Run the desktop API only on the local loopback interface."""
    os.environ['EVERNOTE_DESKTOP_MODE'] = '1'
    WebMigrator().run(
        host='127.0.0.1',
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description='Run the desktop migration backend.')
    parser.add_argument('--port', required=True, type=int)
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    run_backend(args.port, debug=args.debug)


if __name__ == '__main__':
    main()
