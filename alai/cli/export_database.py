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
import alai.wal

logger = logging.getLogger(__name__)


def export_database(ns: Namespace):
    """Export database to ArchLinux-compatible format from internal
    representation.
    """
    config_path: Path = ns.config
    config: Config = Config.from_file(config_path)
    config.repo.package_dir.mkdir(exist_ok=True, parents=True)

    with alai.wal.open(config.repo.wal) as wal:
        output_dir: Path = ns.output_dir
        logger.info('export database to directory %s', output_dir)
        db_path = alai.wal.export_database(wal, config.repo.target_dir,
                                           output_dir, config.repo.name)
        logger.info('database path: %s', db_path)

    db_path_short = db_path.with_suffix('').with_suffix('')
    logger.info('make release symlink: %s', db_path_short)
    if db_path_short.exists():
        db_path_short.unlink()
    db_path_short.symlink_to(db_path.name)

    if ns.release:
        db_path_release = db_path_short.with_name(f'{config.repo.name}.db')
        logger.info('make release symlink: %s', db_path_release)
        if db_path_release.exists():
            db_path_release.unlink()
        db_path_release.symlink_to(db_path_short.name)


parser = subparsers.add_parser(
    'export-database', description=export_database.__doc__,
    help='export ArchLinux package database')
parser.set_defaults(func=export_database)
parser.add_argument('-c', '--config', type=Path, help='repo configuration')
parser.add_argument('-r', '--release', default=False, action='store_true')
parser.add_argument('output_dir', type=Path, help='where to export database')
