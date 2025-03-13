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
import pickle
from argparse import Namespace
from pathlib import Path

from alai.cli.main import subparsers
from alai.config import Config
from alai.repo import Repo

logger = logging.getLogger(__name__)


def build_graph(ns: Namespace):
    config: Config = Config.from_file(ns.config)
    logger.info('dependency databases are %s',
                [x.name for x in config.database])

    repo = Repo.from_path(config.repo.package_dir)
    for ix, (_, info) in enumerate(repo.items()):
        logger.info('[%d] %s', ix, info)

    cache_dir = Path('~/.cache/alai').expanduser()
    # TODO(@daskol): Support cache directory.
    # if (val := obj.get('repo', {}).get('cache-dir')) is not None:
    #     cache_dir = Path(val)
    if ns.cache_dir is not None:
        cache_dir = Path(ns.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    logger.info('store build-graph into %s', cache_dir)
    with open(cache_dir / 'repo.pkl', 'wb') as fout:
        pickle.dump(repo, fout)


parser = subparsers.add_parser(
    'build-graph', description=build_graph.__doc__,
    help='build dependency graph')
parser.set_defaults(func=build_graph)
parser.add_argument('--dry-run', default=False, action='store_true')
parser.add_argument('config', type=Path, help='path to repo spec')

g_dir = parser.add_argument_group('directory options')
g_dir.add_argument(
    '--base-dir', type=Path, help='root directory for all relative paths')
g_dir.add_argument(
    '--cache-dir', type=Path, help='where to store data between runs')
g_dir.add_argument(
    '--data-dir', type=Path, help='root directory to all datasets')
