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

import json
import logging
import sys
from argparse import Namespace
from pathlib import Path

from alai.cli.main import subparsers
from alai.graph import inverse_edges, resolve_dependencies, subgraph_of

logger = logging.getLogger(__name__)


def query(ns: Namespace):
    deps = resolve_dependencies()  # Dependency graph.
    effs = inverse_edges(deps)  # Effects graph.

    package: Path = ns.package
    logger.info('package %s affects the following packages:', package.name)
    package_lists = subgraph_of(effs, package.name)

    if bool(ns.json):
        json.dump(package_lists, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write('\n')
        sys.stdout.flush()
    else:
        for ix, lst in enumerate(package_lists):
            logger.info('[%d] %s', ix, ' '.join(lst))


parser = subparsers.add_parser(
    'query', description=query.__doc__, help='query package dependencies')
parser.set_defaults(func=query)
parser.add_argument('--dry-run', default=False, action='store_true')
parser.add_argument('--json', default=False, action='store_true')
parser.add_argument('package', type=Path, help='package name of interest')

g_dir = parser.add_argument_group('directory options')
g_dir.add_argument(
    '--base-dir', type=Path, help='root directory for all relative paths')
g_dir.add_argument(
    '--cache-dir', type=Path, help='where to store data between runs')
g_dir.add_argument(
    '--data-dir', type=Path, help='root directory to all datasets')
