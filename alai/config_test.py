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

from alai.config import (
    PacmanConfig, PacmanOptionsConfig, PacmanRepoConfig, load_pacman_config)

curr_dir = Path(__file__).parent


def test_load_pacman_config():
    config = load_pacman_config(curr_dir / 'testdata/pacman.conf')
    assert isinstance(config, PacmanConfig)

    options = config.options
    assert isinstance(options, PacmanOptionsConfig)
    assert options.root_dir == Path('/')
    assert options.hold_pkg == ['pacman', 'glibc']
    assert options.download_user == 'alpm'
    assert options.parallel_downloads == 5
    assert options.check_space
    assert not options.color

    assert len(config.repos) == 2
    assert {'core', 'extra'} == set(config.repos)
    for repo in config.repos.values():
        assert isinstance(repo, PacmanRepoConfig)
        assert repo.server == 'https://geo.mirror.pkgbuild.com/$repo/os/$arch'
