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

import pytest

import alai.wal
from alai.wal import Version, WAL, Package, export_database


class TestVersion:

    def test_from_string(self):
        ver = Version.from_string('0.0.0-1')
        assert ver.components == (0, 0, 0)
        assert ver.release == 1
        assert ver.epoch is None

    def test_from_string_epoch(self):
        ver = Version.from_string('1:0.0.0-1')
        assert ver.components == (0, 0, 0)
        assert ver.release == 1
        assert ver.epoch == 1

    @pytest.mark.parametrize('lhs,rhs', [
        ('0.0.0-1', '0.0.0-1'),
        ('1:0.0.0-1', '1:0.0.0-1'),
    ])
    def test_eq(self, lhs: str, rhs: str):
        this = Version.from_string(lhs)
        that = Version.from_string(rhs)
        assert this == that

    @pytest.mark.parametrize('lhs,rhs', [
        ('0.0.0-1', '1:0.0.0-1'),
        ('1:0.0.0-1', '2:0.0.0-1'),
        ('0.0-1', '0.0.0-1'),
        ('0.0.1-1', '0.0.2-1'),
        ('0.0.0-1', '0.0.0-2'),
    ])
    def test_lt(self, lhs: str, rhs: str):
        this = Version.from_string(lhs)
        that = Version.from_string(rhs)
        assert this < that


class TestWAL:

    def test_open(self, tmp_path: Path):
        wal = WAL.open(tmp_path / 'test.wal')
        wal.close()
        with open(tmp_path / 'test.wal', 'rb') as fin:
            signature = fin.read(8)
        assert signature == WAL.MAGIC


def test_open(tmp_path: Path):
    with alai.wal.open(tmp_path / 'test.wal') as _wal:
        pass


def test_export_database(tmp_path: Path):
    pkg_python = Package('python', '3.13.0-1', [], True)
    pkg = Package('python-test', '0.0.0-1', ['python'])

    # Write dummy package to temp directory for testing.
    pkg_path = tmp_path / 'python-test-0.0.0-1-any.pkg.tar.zst'
    import tarfile
    import zstandard
    from io import BytesIO
    with zstandard.open(pkg_path, 'wb') as fout:
        with tarfile.open(fileobj=fout, mode='w:') as tar:
            buf = BytesIO()
            buf.write(b'# Generated by a test\n')
            buf_size = buf.tell()
            buf.seek(0)
            tar_info = tarfile.TarInfo('test-file')
            tar_info.size = buf_size
            tar.addfile(tar_info, buf)

    with alai.wal.open(tmp_path / 'test.wal') as wal:
        wal.add_package(pkg_python)
        wal.add_package(pkg)
        out_path = Path('/tmp/test')
        db_path = export_database(wal, tmp_path, out_path, 'test')

    with tarfile.open(db_path, 'r:gz') as tar:
        basename = pkg_path.name.removesuffix('-any.pkg.tar.zst')
        tar_info = tar.getmember(f'{basename}/desc')
        assert tar_info.isreg()

        tar_file = tar.extractfile(tar_info.path)
        assert tar_file is not None

        lines = [x.strip() for x in tar_file.readlines()[:3]]
        assert lines[0] == b'%FILENAME%'
        assert lines[1] == pkg_path.name.encode('utf-8')
        assert lines[2] == b''
