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

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import IO, ClassVar, Self


@dataclass(slots=True)
class WAL:
    """Represents a package database as a write-ahead log (WAL) with
    checkpoints.
    """

    fp: IO[bytes]

    MAGIC: ClassVar[bytes] = b'ALAI\x00\x00\x00\x00'

    @classmethod
    def open(cls, path_like: PathLike) -> Self:
        if (path := Path(path_like)).exists():
            raise NotImplementedError
        else:
            fout = path.open('wb')
            fout.write(cls.MAGIC)
            fout.flush()
            return cls(fout)

    def close(self):
        self.fp.flush()
        self.fp.close()

    def flush(self):
        self.fp.flush()


@contextmanager
def open(path_like: PathLike) -> Iterator[WAL]:
    wal = WAL.open(path_like)
    try:
        yield wal
    finally:
        wal.close()
