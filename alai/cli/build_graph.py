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
import subprocess
import tomllib
from argparse import Namespace
from codecs import getreader
from dataclasses import dataclass, field
from io import BytesIO
from os import PathLike
from pathlib import Path
from subprocess import PIPE
from typing import IO, Any, Iterator, Self

from alai.cli.main import subparsers

logger = logging.getLogger(__name__)


@dataclass
class Repo:

    repo_dir: Path

    package_names: list[str]

    def __len__(self) -> int:
        return len(self.package_names)

    def __str__(self) -> str:
        name = self.repo_dir.name
        total = len(self)
        return f'{type(self).__name__}(name={name}, total={total})'

    @classmethod
    def from_path(cls, path: PathLike) -> Self:
        repo_dir = Path(path)
        logger.info('initialize repo from PKGBUILD located at %s', repo_dir)
        package_names = []
        for path in repo_dir.rglob('*/PKGBUILD'):
            package_name = path.parent.name
            logger.debug('found package %s', package_name)
            package_names += [package_name]
        logger.info('found %d packages in total', len(package_names))
        return cls(repo_dir, sorted(package_names))

    def items(self) -> Iterator[tuple[str, Any]]:
        for name in self.package_names:
            yield name, self.get(name)

    def get(self, name):
        obj = load_pkgbuild(self.repo_dir / name / 'PKGBUILD')
        obj.pop('pkgbuild_schema_arrays')
        obj.pop('pkgbuild_schema_strings')
        for key in ('groups', 'optdepends', 'conflicts', 'provides', 'depends',
                    'makedepends', 'checkdepends'):
            if key not in obj:
                obj[key] = []
        for key in ('license', 'pkgdesc'):
            if key not in obj:
                obj[key] = ''
        if (key := 'epoch') not in obj:
            obj[key] = None
        obj.pop('options', None)
        obj.pop('validpgpkeys', None)
        obj.pop('install', None)
        obj.pop('backup', None)
        obj.pop('noextract', None)
        obj.pop('replaces', None)
        obj.pop('changelog', None)
        if 'source' not in obj:
            source = []  # TODO
            for arch in obj.get('arch', []):
                source += obj.get(f'source_{arch}', [])
            obj['source'] = source
        return PackageInfo(**obj)


def expect(r: IO[str], desired: str):
    actual = r.read(len(desired))
    if actual == '':
        raise EOFError
    if actual != desired:
        raise RuntimeError


def consume_word(r: IO[str]) -> str:
    word = []
    while (c := r.read(1)):
        if c.isspace():
            break
        word.append(c)
    return ''.join(word)


def consume_until(r: IO[str], ch: str) -> str:
    chars = []
    while (c := r.read(1)):
        if c in ch:
            break
        chars.append(c)
    return ''.join(chars)


def parse_array(r: IO[str]) -> list[Any]:
    line = r.readline().strip()
    terms = line[1:-1].split(' ')
    if not terms:
        return []

    values: dict[int, Any] = {}
    last_ix = -1
    for term in terms:
        if term.startswith('['):
            pos = term.find(']')
            ix = int(term[1:pos])
            value = term[pos + 2:]
        else:
            ix = last_ix + 1
            value = term

        if value.startswith('"') or value.startswith('\''):
            value = value[1:-1]
        values[ix] = value
        last_ix = ix

    size = max(values.keys()) + 1
    arr = [None] * size
    for ix, value in values.items():
        if not (-size <= ix < size):
            raise RuntimeError
        ix = (ix + size) % size
        arr[ix] = value
    return arr


def parse_scalar(r: IO[str]):
    value = r.readline().strip()
    if value.startswith('"') or value.startswith('\''):
        value = value[1:-1]
    return value


def parse_declare(r: IO[str]) -> tuple[str, Any]:
    expect(r, 'declare -')
    opts = consume_word(r)
    name = consume_until(r, '=')

    # If both options are supplied, -A takes precedence.
    if 'A' in opts:
        raise NotImplementedError
    elif 'a' in opts:
        return name, parse_array(r)
    else:
        return name, parse_scalar(r)


def parse_bash(fileobj: IO[bytes]) -> dict[str, Any]:
    r = getreader('utf-8')(fileobj)
    state: dict[str, Any] = {}
    while True:
        try:
            name, value = parse_declare(r)
        except EOFError:
            return state
        else:
            if name in state:
                logger.warning(
                    'variables `%s` is already bound to `%s`: overwriting',
                    name, state[name])
            state[name] = value


def load_pkgbuild(path: Path) -> dict[str, Any]:
    cmd = ['/usr/bin/bash', 'script/pkginfo.sh', str(path)]
    logger.debug('run command: %s', ' '.join(cmd))
    try:
        proc = subprocess.run(cmd, check=True, stdout=PIPE, stderr=PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError() from e  # TODO(@daskol): Display stderr.
    else:
        return parse_bash(BytesIO(proc.stdout))


@dataclass
class PackageSchema:
    pass


@dataclass
class PackageInfo:

    pkgbase: str
    pkgname: str
    pkgver: str
    pkgrel: str
    pkgdesc: str

    epoch: str | None
    arch: list[str]
    license: str
    url: str

    groups: list[str]
    depends: list[str]
    makedepends: list[str]
    checkdepends: list[str]
    optdepends: list[str]

    conflicts: list[str]
    provides: list[str]

    source: list[str]

    b2sums: list[str] = field(default_factory=list)

    md5sums: list[str] = field(default_factory=list)

    sha1sums: list[str] = field(default_factory=list)
    sha224sums: list[str] = field(default_factory=list)
    sha256sums: list[str] = field(default_factory=list)
    sha384sums: list[str] = field(default_factory=list)
    sha512sums: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        if self.epoch:
            epoch = f'{self.epoch}:'
        else:
            epoch = ''
        args = ', '.join([
            f'name={self.pkgname}',
            f'ver={self.pkgver}-{self.pkgrel}',
            f'url={self.url}',
        ])
        return f'{type(self).__name__}({args})'


def build_graph(ns: Namespace):
    spec_path: Path = ns.config
    with open(spec_path, 'rb') as fin:
        obj = tomllib.load(fin)
    sources = obj.get('source', [])
    logger.info('dependency sources are %s', sources)

    repo_config = obj.get('repo')
    repo = Repo.from_path(repo_config['repo'])
    for ix, (_, info) in enumerate(repo.items()):
        logger.info('[%d] %s', ix, info)

    cache_dir = Path('~/.cache/alai').expanduser()
    if (val := obj.get('repo', {}).get('cache-dir')) is not None:
        cache_dir = Path(val)
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
