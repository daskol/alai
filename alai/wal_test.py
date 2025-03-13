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

from pathlib import Path

import alai.wal
from alai.wal import WAL


class TestWAL:

    def test_open(self, tmp_path: Path):
        wal = WAL.open(tmp_path / 'test.wal')
        wal.close()
        with open(tmp_path / 'test.wal', 'rb') as fin:
            signature = fin.read(8)
        assert signature == WAL.MAGIC


def test_open(tmp_path):
    with alai.wal.open(tmp_path / 'test.wal') as wal:
        pass
