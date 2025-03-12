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

import re
import warnings
from enum import IntEnum
from os import PathLike
from pathlib import Path
from types import UnionType
from typing import IO, Any, Literal, cast, get_args, get_origin

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

MAKEPKG_CONF = Path('/etc/makepkg.conf')

PACMAN_CONF = Path('/etc/pacman.conf')


class CleanMethod(IntEnum):

    KeepInstalled = 0b01  # 1
    KeepCurrent = 0b10  # (1 << 1)


class PacmanOptionsConfig(BaseModel):
    """Section `options` of `pacman.conf`."""

    root_dir: Path = Path('/')
    db_path: Path = Path('/var/lib/pacman')
    cache_dir: Path = Path('/var/cache/pacman/pkg')
    hook_dir: Path = Path('/usr/share/libalpm/hooks/')
    gpg_dir: Path = Path('/etc/pacman.d/gnupg')
    log_file: Path = Path('/var/log/pacman.log')

    hold_pkg: list[str] = Field(default_factory=list)
    ignore_pkg: list[str] = Field(default_factory=list)
    ignore_group: list[str] = Field(default_factory=list)
    no_upgrade: list[str] = Field(default_factory=list)
    no_extract: list[str] = Field(default_factory=list)

    architecture: list[str] = Field(default_factory=list)

    xfer_command: str | None = None

    clean_method: CleanMethod = CleanMethod.KeepInstalled

    sig_level: list[str] = Field(default_factory=list)
    local_file_sig_level: list[str] = Field(default_factory=list)
    remote_file_sig_level: list[str] = Field(default_factory=list)

    download_user: str | None = None
    parallel_downloads: int = 5

    check_space: bool = False
    color: bool = False
    disable_download_timeout: bool = False
    disable_sandbox: bool = False
    i_love_candy: bool = False
    no_progress_bar: bool = False
    use_syslog: bool = False
    verbose_pkg_lists: bool = False

    # TODO(@daskol): os.uname for architecture
    # TODO(@daskol): current user for download_user


class PacmanRepoConfig(BaseModel):
    """Repository of `pacman.conf`."""

    server: str
    cache_server: str | None = None
    sig_level: list[str] = FieldInfo(default_factory=list)
    usage: list[str] = FieldInfo(default_factory=list)  # TODO


def get_schema(cls: BaseModel) -> dict[str, tuple[str, Any]]:
    """Return schema of `pacman.conf` (types and field names)."""
    letter = re.compile(r'(^|_)(\w)')
    schema: dict[str, dict[str, Any]] = {}
    info: FieldInfo
    for name, info in cls.model_fields.items():
        match name:
            case 'db_path':
                conf_name = 'DBPath'
            case 'gpg_dir':
                conf_name = 'GPGDir'
            case _:
                conf_name = letter.sub(lambda m: m.group(2).upper(), name)
        if (origin := get_origin(info.annotation)) is not None:
            if origin is list:
                factory = parse_list
            elif issubclass(origin, UnionType):
                args = get_args(info.annotation)
                factory, *_ = args
        else:
            factory = info.annotation
        schema[name] = (conf_name, factory)
    return schema


class PacmanConfig(BaseModel):

    options: PacmanOptionsConfig

    repos: dict[str, PacmanRepoConfig] = Field(default_factory=list)


def parse_list(value: str) -> list[str]:
    return value.split(' ')


def parse_pacman_config(
        fin: IO[str]) -> dict[str, dict[str | None, str | None]]:
    # TODO(@daskol): No limit on line width.
    key: str
    val: str | None = None
    section: str | None = None
    sections: dict[str | None, dict[str, str | None]] = {}
    for ix, line in enumerate(fin, 1):
        line = line.removesuffix('\n')

        # Blank line or line comment.
        if line == '' or line.startswith('#'):
            continue

        # Section header.
        if line[0] == '[' and line[-1] == ']':
            section = line[1:-1]
            sections[section] = {}
            continue

        parts = [x.strip() for x in line.split('=', 1)]
        if len(parts) == 2:
            key, val = parts
        else:
            key, val = parts[0], None

        # TODO(@daskol): Handle Include directive.
        if section is None and None not in sections:
            sections[None] = {}

        sections[section][key] = val
    # TODO(@daskol): Process Include directives.
    return sections


def load_pacman_config(path: PathLike = PACMAN_CONF) -> PacmanConfig:
    with open(path) as fin:
        result = parse_pacman_config(fin)
    if None in result:
        raise RuntimeError('Section-free key-values are not allowed.')
    sections = cast(dict[str, dict[str, str | None]], result)

    # Process `options` section.
    section = sections.pop('options', {})
    if 'Include' in section:
        warnings.warn(
            ('Include directive is not supported in `options` section of '
             '`pacman.conf`.'), RuntimeWarning)
    schema = get_schema(PacmanOptionsConfig)
    kwargs = {}
    for key, (opt, cls) in schema.items():
        if (val := section.get(opt)) is not None:
            kwargs[key] = cls(val)
        elif cls is bool and opt in section:
            kwargs[key] = True
    options = PacmanOptionsConfig(**kwargs)

    # Process repositories.
    repos: dict[str, PacmanRepoConfig]= {}
    repo_schema = get_schema(PacmanRepoConfig)
    for name, section in sections.items():
        if (include := section.pop('Include', None)) is not None:
            with open(path.parent / include) as fin:
                subconf = parse_pacman_config(fin)
            if included := subconf.get(None, {}):
                section.update(included)

        kwargs = {}
        for key, (opt, cls) in repo_schema.items():
            if (val := section.get(opt)) is not None:
                kwargs[key] = cls(val)
        repos[name] = PacmanRepoConfig(**kwargs)

    return PacmanConfig(options=options, repos=repos)


class Config(BaseModel):
    pass
