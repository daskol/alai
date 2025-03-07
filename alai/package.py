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
import subprocess
from codecs import getreader
from io import BytesIO
from pathlib import Path
from subprocess import PIPE
from typing import IO, Any

logger = logging.getLogger(__name__)


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
