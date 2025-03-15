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


def prepare_package(package_name: str, package_dir: Path,
                    external=False) -> Package:
    if external:
        pkg_info = find_package(package_name)
        pkg_version = '0.0.0-1'  # TODO(@daskol)
        return Package(pkg_info.name, pkg_version, [], external=True)
    else:
        logger.info('load package info from `PKGBUILD` at %s', package_dir)
        repo = Repo.from_path(package_dir)
        pkg_info = repo.get(package_name)
        return Package(name=pkg_info.name, version=pkg_info.version,
                       depends=pkg_info.depends)


def update_package(ns: Namespace):
    """Update package in database."""
    config_path: Path = ns.config
    config: Config = Config.from_file(config_path)
    config.repo.package_dir.mkdir(exist_ok=True, parents=True)

    package_path: Path = ns.package
    logger.info('prepare package metadata: %s', package_path)
    pkg = prepare_package(package_path, config.repo.package_dir, ns.external)

    with alai.wal.open(config.repo.wal) as wal:
        logger.info('insert known missing external dependencies')
        for dep_name in pkg.depends:
            if (dep := find_package(dep_name)) is None:
                logger.error('unknown package dependency: %s', dep_name)
                return 1
            if wal.get(dep_name) is None:
                dep_version = '0.0.0-1'  # TODO(@daskol): Retrieve version.
                dep_pkg = Package(dep.name, dep_version, [], True)
                wal.add_package(dep_pkg)

        # TODO(@daskol): Remove needless dependencies.

        logger.info('try to update package into database: %s-%s', pkg.name,
                    pkg.version)
        try:
            wal.update_package(pkg)
        except Exception:
            logger.exception('failed to add package %s to database', pkg.name)


parser = subparsers.add_parser(
    'update-package', description=update_package.__doc__,
    help='add package to database')
parser.set_defaults(func=update_package)
parser.add_argument('-e', '--external', default=False, action='store_true')
parser.add_argument('config', type=Path, help='path to repo configuration')
parser.add_argument('package', type=Path, help='path to package')
