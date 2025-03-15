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

import alai.wal
from alai.cli.main import subparsers
from alai.config import Config
from alai.extension import find_package
from alai.repo import Repo
from alai.wal import Package

logger = logging.getLogger(__name__)


def remove_package(ns: Namespace):
    """Remove package from repository database."""
    config_path: Path = ns.config
    config: Config = Config.from_file(config_path)
    config.repo.package_dir.mkdir(exist_ok=True, parents=True)

    with alai.wal.open(config.repo.wal) as wal:
        # TODO(@daskol): Remove needless dependencies.
        package_name: str = ns.package
        logger.info('try to remove package %s from database', package_name)
        try:
            wal.remove_package(package_name)
        except Exception:
            logger.exception('failed to remove package %s from database',
                             package_name)


parser = subparsers.add_parser(
    'remove-package', description=remove_package.__doc__,
    help='remove package to database')
parser.set_defaults(func=remove_package)
parser.add_argument('config', type=Path, help='path to repo configuration')
parser.add_argument('package', type=str, help='path to package')
