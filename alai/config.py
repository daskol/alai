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

from os import PathLike
from pathlib import Path
from typing import IO, Literal

from pydantic import BaseModel, Field

__all__ = ('Config', 'MAKEPKG_CONF', 'PACMAN_CONF')

MAKEPKG_CONF = Path('/etc/makepkg.conf')

PACMAN_CONF = Path('/etc/pacman.conf')

SigLevel = Literal['never', 'optional', 'always']


class PacmanRepoConfig(BaseModel):

    server: str
    cache_server: str | None = None
    sig_level: SigLevel = 'optional'
    usage: int = 0  # TODO


class PacmanConfig(BaseModel):

    DBPath: Path = Path('/var/lib/pacman')
    GPGDir: Path = Path('/etc/pacman.d/gnupg')
    LogFile: Path = Path('/var/log/pacman.log')
    RootDir: Path = Path('/')

    Architecture: list = Field(default_factory=list)
    CacheDir: list = Field(default_factory=list)
    CleanMethod: list = Field(default_factory=list)
    HoldPkg: list = Field(default_factory=list)
    HookDir: list = Field(default_factory=list)
    IgnoreGroup: list = Field(default_factory=list)
    IgnorePkg: list = Field(default_factory=list)
    LocalFileSigLevel: list = Field(default_factory=list)
    NoExtract: list = Field(default_factory=list)
    NoUpgrade: list = Field(default_factory=list)
    RemoteFileSigLevel: list = Field(default_factory=list)
    SigLevel: list = Field(default_factory=list)

    DownloadUser: str = 'TODO'
    XferCommand: str = 'TODO'
    ParallelDownloads: int = 5

    CheckSpace: bool = False
    Color: bool = False
    DisableDownloadTimeout: bool = False
    DisableSandbox: bool = False
    ILoveCandy: bool = False
    NoProgressBar: bool = False
    UseSyslog: bool = False
    VerbosePkgLists: bool = False

    repos: list[PacmanRepoConfig] = Field(default_factory=list)


def parse_pacman_config(fin: IO[str]) -> dict[str, dict[str, str | None]]:
    # TODO(@daskol): No limit on line width.
    key: str
    val: str | None = None
    section: str | None = None
    sections: dict[str, dict[str, str | None]] = {}
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
        sections[section][key] = val
    # TODO(@daskol): Process Include directives.
    return sections


def load_pacman_config(path: PathLike = PACMAN_CONF) -> PacmanConfig:
    with open(path) as fin:
        sections = parse_pacman_config(fin)

    SCHEMA = {'db_path': ('DBPath', Path)}

    options = sections.pop('options', {})
    kwargs = {}
    for key, (opt, cls) in SCHEMA.items():
        if (val := options.get(opt)) is not None:
            kwargs[key] = cls(val)

    repos = []
    for name, secion in sections.items():
        repos += [PacmanRepoConfig(server='TODO')]

    return PacmanConfig(**kwargs, repos=repos)


class Config(BaseModel):
    pass
