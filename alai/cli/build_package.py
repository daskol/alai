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

from argparse import Namespace
from pathlib import Path

from alai.cli.main import subparsers


def build_package(ns: Namespace):
    pass


parser = subparsers.add_parser(
    'build-package', description=build_package.__doc__, help='build package')
parser.set_defaults(func=build_package)
parser.add_argument('--dry-run', default=False, action='store_true')
parser.add_argument('package', type=Path, help='package to build')

g_dir = parser.add_argument_group('directory options')
g_dir.add_argument(
    '--base-dir', type=Path, help='root directory for all relative paths')
g_dir.add_argument(
    '--cache-dir', type=Path, help='where to store data between runs')
g_dir.add_argument(
    '--data-dir', type=Path, help='root directory to all datasets')
