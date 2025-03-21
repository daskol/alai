# Copyright 2025 Archlinux AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import sys
from argparse import ArgumentParser, FileType, Namespace
from asyncio import run
from inspect import iscoroutinefunction
from sys import stderr

try:
    from alai.version import __version__
except ImportError:
    __version__ = None


LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warn': logging.WARNING,
    'error': logging.ERROR,
}

LOGGING_FMT = '%(levelname)s %(asctime)s %(module)s %(message)s'

LOGGING_DATEFMT = '%Y-%m-%d %H:%M:%S'


class Formatter(logging.Formatter):

    def __init__(self, *args, is_tty=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_tty = is_tty

    def format(self, record):
        ch = record.levelname[:1]
        if self.is_tty:
            match ch:
                case 'W':
                    ch = f'\033[33m{ch}\033[0m'
                case 'E' | 'F':
                    ch = f'\033[31m{ch}\033[0m'
        record.levelname = ch
        return super().format(record)


def help_(ns: Namespace):
    parser.print_help()


def version(ns: Namespace):
    print('version', __version__)


def main():
    args: Namespace = parser.parse_args()
    # Parse command line arguments. If no subcommand were run then show usage
    # and exit. We assume that only main parser (super command) has valid value
    # in func attribute.
    args = parser.parse_args()
    if args.func is None:
        parser.print_usage()
        return

    # Set up basic logging configuration.
    if (stream := args.log_output) is None:
        stream = stderr

    # Configure loggers.
    logging.basicConfig(format=LOGGING_FMT, datefmt=LOGGING_DATEFMT,
                        level=logging.WARNING, stream=stream)

    # Configure package-level logger.
    formatter = Formatter(fmt=LOGGING_FMT, datefmt=LOGGING_DATEFMT,
                          is_tty=stream.isatty())
    console_handler = logging.StreamHandler(stream)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(LOG_LEVELS[args.log_level])

    logger = logging.getLogger('alai')
    logger.setLevel(LOG_LEVELS[args.log_level])
    logger.addHandler(console_handler)
    logger.propagate = False

    # Dispatch CLI subcommand to corresponding handler.
    if iscoroutinefunction(args.func):
        code = run(args.func(args))
    else:
        code = args.func(args)

    if code is not None:
        sys.exit(code)


parser = ArgumentParser(description=__doc__)
parser.set_defaults(func=None)

# Describe `logging` group.
g_log = parser.add_argument_group('logging options')
g_log.add_argument(
    '--log-level', default='info', choices=sorted(LOG_LEVELS.keys()),
    help='set logger verbosity level')
g_log.add_argument(
    '--log-output', default=stderr, metavar='FILENAME', type=FileType('w'),
    help='set output file or stderr (-) for logging')

# Describe subparsers for subcommands.
subparsers = parser.add_subparsers(title='subcommands')

# Describe subcommand `help`.
p_help = subparsers.add_parser(
    'help', add_help=False, help='show this message and exit')
p_help.set_defaults(func=help_)

# Describe subcommand `version`.
p_version = subparsers.add_parser(
    'version', add_help=False, help='show version')
p_version.set_defaults(func=version)
