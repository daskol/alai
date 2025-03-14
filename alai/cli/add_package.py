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
from shutil import copyfile

import alai.wal
from alai.cli.main import subparsers
from alai.config import Config
from alai.extension import find_package
from alai.repo import Repo
from alai.wal import Package

logger = logging.getLogger(__name__)


ARCHIVE_GLOBS = [
    '*.tar.*', '*.7z', '*.jar', '*.rar', '*.zip', '*.gz', '*.gzip', '*.tgz',
    '*.bzip', '*.bzip2', '*.bz2', '*.xz', '*.lzma', '*.cab', '*.xar', '*.zst',
    '*.tzst', '*.iso', '*.tar', '*.dmg', '*.xpi', '*.gem', '*.whl', '*.egg',
    '*.deb', '*.rpm', '*.msi', '*.msm', '*.msp', '*.txz'
]


def relocate_package(package_path: Path, package_dir: Path) -> Package:
    if not package_path.exists():
        logger.error('no such package found: %s', package_path)
        return 1
    if not package_path.is_dir():
        logger.error('package must correspond to a directory with `PKGBUILD`')
        return 1

    src = package_path
    dst = package_dir / package_path.name
    if not dst.exists():
        paths: list[Path] = []
        for path in src.iterdir():
            # Copy only files.
            if path.is_dir():
                continue
            # But not archives.
            for glob in ARCHIVE_GLOBS:
                if path.match(glob):
                    break
            else:
                paths.append(path)

        logger.info('copy %d files', len(paths))
        dst.mkdir(exist_ok=True)
        for path in paths:
            logger.info('copy %s to %s', path, dst)
            copyfile(path, dst / path.name)

    logger.info('check package consistency')
    for filename in ('PKGBUILD', '.SRCINFO'):
        if not (src / filename).exists():
            logger.error('no file `%s` in package source directory %s',
                         filename, dst)
            return 1

    logger.info('load package info from `PKGBUILD`')
    repo = Repo.from_path(package_dir)
    pkg_info = repo.get(package_path.name)
    return Package(name=pkg_info.name, version=pkg_info.version,
                   depends=pkg_info.depends)


def prepare_package(package_path: Path, package_dir: Path,
                    external=False) -> Package:
    if external:
        if len(package_path.parts) > 1:
            logger.error(
                'external package requires package name but not path: %s',
                package_path)
            exit(1)  # TODO
        pkg_info = find_package(package_path.name)
        pkg_version = '0.0.0-1'  # TODO(@daskol)
        return Package(pkg_info.name, pkg_version, [], external=True)
    else:
        return relocate_package(package_path, package_dir)


def add_package(ns: Namespace):
    """Add package to the repository database.

    Package is specified as a path to directory containing `PKGBUILD` file.
    This directory will be copied to to `repo.package_dir`. On success, the
    repository database will be updated with `add-package` record.
    """
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

        logger.info('try to insert package to database: %s-%s', pkg.name,
                    pkg.version)
        try:
            wal.add_package(pkg)
        except Exception:
            logger.exception('failed to add package %s to database', pkg.name)


parser = subparsers.add_parser(
    'add-package', description=add_package.__doc__,
    help='add package to database')
parser.set_defaults(func=add_package)
parser.add_argument('config', type=Path, help='path to repo configuration')
parser.add_argument('package', type=Path, help='path to package')

parser.add_argument('-e', '--external', default=False, action='store_true')
