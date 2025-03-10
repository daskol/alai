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

from alai.config import PacmanConfig, load_pacman_config


def test_load_pacman_config():
    config = load_pacman_config()
    from pprint import pprint
    pprint(config)
    assert isinstance(config, PacmanConfig)
    assert len(config.repos) == 2
