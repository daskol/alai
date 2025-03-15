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
import tarfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from hashlib import file_digest, sha256
from io import BytesIO
from os import PathLike
from pathlib import Path
from typing import IO, ClassVar, Literal, Self, cast

import zstandard

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Version:
    """Internal version representation."""

    components: tuple[int | str, ...]
    release: int
    epoch: int | None = None

    def __post_init__(self):
        if self.release <= 0:
            raise RuntimeError(
                f'Release number must be positive: {self.release}.')

    def __eq__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        that: Version = cast(Version, other)
        return (self.epoch == that.epoch and
                self.components == that.components and
                self.release == that.release)

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        that: Version = cast(Version, other)

        match (self.epoch is None, that.epoch is None):
            case (False, False):
                if self.epoch < that.epoch:
                    return True
            case (True, False):
                return True
            case (False, True):
                return False
            case (True, True):
                pass

        if self.components < that.components:
            return True
        else:
            return self.release < that.release

    def __le__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        that: Version = cast(Version, other)
        return self < that or self == that

    def __str__(self) -> str:
        components = '.'.join(str(x) for x in self.components)
        if self.epoch:
            return f'{self.epoch}:{components}-{self.release}'
        else:
            return f'{components}-{self.release}'

    @classmethod
    def from_string(cls, version: str) -> Self:
        epoch: int | None
        if len(parts := version.split(':', 1)) == 1:
            epoch = None
        else:
            epoch = int(parts[0])
            version = parts[1]

        version, release_str = version.split('-', 1)
        release = int(release_str)

        components = []
        for ent in version.split('.'):
            try:
                components += [int(ent)]
            except ValueError:
                components += [ent]

        return cls(tuple(components), release, epoch)


@dataclass(slots=True)
class Package:
    name: str
    version: str
    depends: list[str]
    external: bool = False
    arch: str = 'any'


@dataclass(slots=True)
class State:
    """Represent consistent repository state."""

    revision: int = 0

    packages: dict[str, Package] = field(default_factory=dict)


@dataclass(slots=True)
class WAL:
    """Represents a package database as a write-ahead log (WAL) with
    checkpoints.
    """

    fp: IO[bytes]

    state: State = field(default_factory=State)

    mode: Literal['init', 'replaying', 'ready'] = 'init'

    MAGIC: ClassVar[bytes] = b'ALAI\x00\x00\x00\x00'

    @classmethod
    def open(cls, path_like: PathLike) -> Self:
        if (path := Path(path_like)).exists():
            fp = path.open('r+b')
            if (magic := fp.read(8)) != cls.MAGIC:
                raise RuntimeError(f'Wrong file signature: {magic}.')
            wal = cls(fp)
            wal.play()
            return wal
        else:
            fp = path.open('wb')
            fp.write(cls.MAGIC)
            fp.flush()
            return cls(fp)

    def close(self):
        self.fp.flush()
        self.fp.close()

    def flush(self):
        self.fp.flush()

    def play(self):
        logger.info('play write-ahead log')
        self.mode = 'replaying'
        rev = 0
        for rev, line in enumerate(self.fp, 1):
            obj = json.loads(line)
            match obj.get('op'):
                case None:
                    raise RuntimeError('Corrupted WAL: missing op.')
                case 'add-package':
                    package = Package(**obj.get('args'))
                    self.add_package(package)
                case 'update-package':
                    package = Package(**obj.get('args'))
                    self.update_package(package)
                case _:
                    logger.warn('unknown op %s: ignoring', RuntimeWarning)
        self.mode = 'ready'
        self.state.revision = rev

    def append(self, op: str, **kwargs):
        """Append a record to database log file."""
        if self.mode != 'ready':
            return
        record = {'op': op, 'args': kwargs}
        line = json.dumps(record, ensure_ascii=False, indent=None)
        self.fp.write(line.encode('utf-8'))
        self.fp.write(b'\n')

    def add_package(self, package: Package):
        logger.info('add package %s', package.name)
        if package.name in self.state.packages:
            raise KeyError(f'Package {package.name} is already in database.')

        # Verify package dependencies.
        for dep in package.depends:
            if dep not in self.state.packages:
                raise RuntimeError(f'Unknown package dependency: {dep}.')

        self.state.packages[package.name] = package
        self.append('add-package', **asdict(package))

    def update_package(self, package: Package):
        logger.info('update package %s', package.name)
        if package.name not in self.state.packages:
            raise KeyError(f'No package {package.name} in database.')

        # Verify version of updated package.
        prev_pkg = self.state.packages[package.name]
        prev_ver = Version.from_string(prev_pkg.version)
        next_ver = Version.from_string(package.version)
        if prev_ver >= next_ver:
            raise RuntimeError(
                'Version of updated package must be strictly increasing: '
                f'{prev_ver} >= {next_ver}.')

        # Verify package dependencies.
        for dep in package.depends:
            if dep not in self.state.packages:
                raise RuntimeError(f'Unknown package dependency: {dep}.')

        self.state.packages[package.name] = package
        self.append('update-package', **asdict(package))

    def get(self, package_name: str) -> Package | None:
        return self.state.packages.get(package_name)


@contextmanager
def open(path_like: PathLike) -> Iterator[WAL]:
    wal = WAL.open(path_like)
    try:
        yield wal
    finally:
        wal.close()


def export_database(wal: WAL, package_dir: Path, output_dir: Path,
                    name: str) -> Path:
    buf = BytesIO()

    def write(key: str, val: str | int | list[str]):
        buf.write(b'%')
        buf.write(key.encode('utf-8'))
        buf.write(b'%\n')
        match val:
            case int():
                buf.write(str(val).encode('utf-8'))
                buf.write(b'\n')
            case str():
                buf.write(val.encode('utf-8'))
                buf.write(b'\n')
            case list():
                for ent in val:
                    buf.write(ent.encode('utf-8'))
                    buf.write(b'\n')
        buf.write(b'\n')

    output_dir.mkdir(exist_ok=True, parents=True)
    path = output_dir / f'{name}-r{wal.state.revision}.db.tar.gz'

    with tarfile.open(path, 'w:gz') as tar:
        for pkg in (x for x in wal.state.packages.values() if not x.external):
            basename = f'{pkg.name}-{pkg.version}'
            filename = f'{basename}-{pkg.arch}.pkg.tar.zst'
            pkg_path = (package_dir / filename)
            pkg_csize = pkg_path.stat().st_size
            pkg_isize = 0
            with zstandard.open(pkg_path, 'rb') as fin:
                with tarfile.open(fileobj=fin, mode='r:') as pkg_tar:
                    for ent in pkg_tar.getmembers():
                        if ent.name in ('.BUILDINFO', '.MTREE', '.PKGINFO'):
                            continue
                        pkg_isize += ent.size

            with pkg_path.open('rb') as fin:
                sha256sum = file_digest(fin, sha256).hexdigest()

            buf.seek(0)
            write('FILENAME', filename)
            write('NAME', pkg.name)
            write('BASE', pkg.name)  # TODO
            write('VERSION', pkg.version)
            write('DESC', 'TODO')
            write('CSIZE', pkg_csize)
            write('ISIZE', pkg_isize)
            write('SHA256SUM', sha256sum)
            write('URL', 'https://example.org')
            write('LICENSE', 'TODO')
            write('ARCH', pkg.arch)
            write('BUILDDATE', int(datetime.now().timestamp()))
            write('PACKAGER', 'Daniel Bershatsky <d.bershatsky2@skoltech.ru>')
            write('DEPENDS', pkg.depends)
            write('MAKEDEPENDS', [])
            size = buf.tell()
            buf.seek(0)

            tar_info = tarfile.TarInfo(basename)
            tar_info.type = tarfile.DIRTYPE
            tar.addfile(tar_info)

            tar_info = tarfile.TarInfo(f'{basename}/desc')
            tar_info.size = size
            tar.addfile(tar_info, buf)

    return path
