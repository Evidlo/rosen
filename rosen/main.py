#!/usr/bin/env python3

import argparse
import logging

from rosen.client import run, shell
from rosen.server import server
from rosen.tui import tui
from rosen.down import down_file

logging.basicConfig(format='%(asctime)s line %(lineno)d: %(message)s')
log = logging.getLogger('rosen')

def main():
    parser = argparse.ArgumentParser(description="SEAQUE ground station")
    parser._positionals.title = "commands"

    subparsers = parser.add_subparsers()
    subparsers.required = True

    # program arguments
    parser.add_argument('--debug', action='store_true', default=False, help="enable debugging")
    # parser.add_argument('--host', metavar='HOST', default='127.0.0.1', type=str, help="SEAQUE host")
    # parser.add_argument('--port', metavar='PORT', default=8000, type=int, help="SEAQUE port")

    # TODO: Can change the default back to above, this is just to make it easier for testing
    parser.add_argument('--host', metavar='HOST', default='192.168.215.2', type=str, help="SEAQUE host")
    parser.add_argument('--port', metavar='PORT', default=10888, type=int, help="SEAQUE port")

    # subparser for `run` command
    run_parser = subparsers.add_parser('run', help="run a GCOMM script file")
    run_parser.add_argument('--loop', action='store_true', default=False, help="loop forever")
    run_parser.add_argument('script', nargs='?', metavar='PATH', type=str, default='gcomm.script', help="script path")
    run_parser.set_defaults(func=run)

    shell_parser = subparsers.add_parser('shell', help="run GCOMM commands interactively")
    shell_parser.add_argument('--script', metavar='PATH', type=str, default=None, help='Optional Python script containing variables to be made available in the shell')
    shell_parser.set_defaults(func=shell)

    server_parser = subparsers.add_parser('server', help="run a test echo server")
    server_parser.set_defaults(func=server)

    # TUI parser
    tui_parser = subparsers.add_parser('tui', help='run the rosen interactive TUI')
    tui_parser.add_argument('--logfile', metavar='PATH', type=str, default=None, help='pkl file to log an array of packets to')
    tui_parser.set_defaults(func=tui)

    # Download parser
    down_parser = subparsers.add_parser('download', help='Download a file from SEAQUE')
    down_parser.add_argument('--downfile', metavar='PATH', type=str, default='down.bin', help='Name of file to download')
    down_parser.set_defaults(func=down_file)

    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)
        log.debug("Debugging enabled")

    try:
        args.func(args)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
