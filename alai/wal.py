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
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from os import PathLike
from pathlib import Path
from typing import IO, ClassVar, Literal, Self

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Package:
    name: str
    version: str
    depends: list[str]
    external: bool = False


@dataclass(slots=True)
class State:
    """Represent consistent repository state."""

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
        for _, line in enumerate(self.fp):
            obj = json.loads(line)
            match obj.get('op'):
                case None:
                    raise RuntimeError('Corrupted WAL: missing op.')
                case 'add-package':
                    package = Package(**obj.get('args'))
                    self.add_package(package)
                case _:
                    logger.warn('unknown op %s: ignoring', RuntimeWarning)
        self.mode = 'ready'

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

    def get(self, package_name: str) -> Package | None:
        return self.state.packages.get(package_name)


@contextmanager
def open(path_like: PathLike) -> Iterator[WAL]:
    wal = WAL.open(path_like)
    try:
        yield wal
    finally:
        wal.close()
