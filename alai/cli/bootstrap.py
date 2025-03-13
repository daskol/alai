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
from argparse import Namespace
from pathlib import Path

from alai.cli.main import subparsers
from alai.config import Config
from alai.wal import WAL

logger = logging.getLogger(__name__)


def bootstrap(ns: Namespace):
    config_path: Path = ns.config
    config: Config = Config.from_file(config_path)
    print(config)
    wal = WAL.open(config.repo.wal)
    wal.close()


parser = subparsers.add_parser(
    'bootstrap', description=bootstrap.__doc__,
    help='bootstrap package database')
parser.set_defaults(func=bootstrap)
parser.add_argument('config', type=Path, help='path to repo configuration')
