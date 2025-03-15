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
from os import getenv
from pathlib import Path
from subprocess import run

from alai.cli.main import subparsers
from alai.config import Config
from alai.repo import Repo

logger = logging.getLogger(__name__)


def build_package(ns: Namespace):
    """Build package managed by repository database."""
    config_path: Path = ns.config
    config: Config = Config.from_file(config_path)
    for path in (config.repo.package_dir, config.repo.target_dir,
                 config.repo.source_dir):
        path.mkdir(exist_ok=True, parents=True)

    package_name: str = ns.package
    if not (work_dir := config.repo.package_dir / package_name).exists():
        logger.error('no package directory: %s', work_dir)
        return 1

    # TODO(@daskol): Configure shell and location of ABS.
    cmd = ['/bin/bash', '-c', '/usr/bin/makepkg -Ccs --nocheck --nosign']
    env = {'PKGDEST': str(config.repo.target_dir.absolute()),
           'SRCDEST': str(config.repo.source_dir.absolute()),
           'PATH': getenv('PATH')}
    proc = run(args=cmd, env=env, cwd=work_dir)
    if proc.returncode != 0:
        logger.error('failed to build package %s', package_name)
        return 1

    # Prepare filename of target package.
    repo = Repo.from_path(config.repo.package_dir)
    pkg_info = repo.get(package_name)
    if 'any' in pkg_info.arch:
        arch = 'any'
    elif 'x86_64' in pkg_info.arch:
        arch = 'x86_64'
    else:
        raise RuntimeError(f'Unsupported package arch: {pkg_info.arch}.')
    pkg_file = f'{pkg_info.name}-{pkg_info.version}-{arch}.pkg.tar.zst'
    pkg_path = config.repo.target_dir / pkg_file
    logger.info('package located at %s', pkg_path)


parser = subparsers.add_parser(
    'build-package', description=build_package.__doc__, help='build package')
parser.set_defaults(func=build_package)
parser.add_argument('-c', '--config', type=Path, help='repository config')
parser.add_argument('package', type=Path, help='package to build')
