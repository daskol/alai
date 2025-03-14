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
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from typing import Any, Iterator, Self

from alai.package import load_pkgbuild

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

    @property
    def name(self) -> str:
        return self.pkgname

    @property
    def version(self) -> str:
        if self.epoch:
            return f'{self.epoch}:{self.pkgver}-{self.pkgrel}'
        else:
            return f'{self.pkgver}-{self.pkgrel}'

    def __repr__(self) -> str:
        if self.epoch:
            epoch = f'{self.epoch}:'
        else:
            epoch = ''
        args = ', '.join([
            f'name={self.pkgname}',
            f'ver={epoch}{self.pkgver}-{self.pkgrel}',
            f'url={self.url}',
        ])
        return f'{type(self).__name__}({args})'
