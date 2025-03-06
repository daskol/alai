# Copyright 2025 ArchLinux AI
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
import pickle
import re
from dataclasses import dataclass
from pathlib import Path

from alai.cli.build_graph import PackageInfo, Repo
from alai.extension import Package, find_package

logger = logging.getLogger(__name__)

RE_COMPARISON = re.compile(r'(==|>=|<=|>|<)')


@dataclass(slots=True)
class Graph:

    nodes: dict[str, PackageInfo | Package]

    links: dict[str, list[str]]


def resolve_dependencies(repo: Repo | None = None):
    # TODO(@daskol): Ad hoc.
    if repo is None:
        cache_dir = Path('~/.cache/alai').expanduser()
        with open(cache_dir / 'repo.pkl', 'rb') as fin:
            repo: Repo = pickle.load(fin)

    # TODO(@daskol): Drop constraints for now.
    def strip(name: str) -> str:
        if (m := RE_COMPARISON.search(name)) is not None:
            name = name[:m.start()]
        return name

    # 1. Populates queue.
    queue: list[str] = []
    for name, _ in repo.items():
        queue += [name]

    # 2. Add package dependencies (node list graph representation).
    nodes: dict[str, PackageInfo | Package] = {}
    links: dict[str, list[str]] = {}  # Required dependencies (childs).
    pkg_info: PackageInfo | Package
    while queue:
        pkg_name, queue = queue[0], queue[1:]
        pkg_name = strip(pkg_name)

        if pkg_name in nodes:
            print(f'[{len(queue)}] {pkg_name} is already resolved')
            continue
        print(f'[{len(queue)}] try to resolve {pkg_name}')

        try:
            pkg_info = repo.get(pkg_name)
        except (KeyError, RuntimeError):
            pkg_info = find_package(pkg_name)

        if pkg_info is None:
            logger.warning('failed to resolve dependency %s', pkg_name)
            print('failed to resolve', pkg_name)
            continue
        else:
            nodes[pkg_name] = pkg_info

        # TODO(@daskol): Skip if package is owned by `core` or `extra`.
        if isinstance(pkg_info, Package):
            continue

        links[pkg_name] = []
        for dep_name in map(strip, pkg_info.depends):
            links[pkg_name].append(dep_name)
            queue.append(dep_name)

    print()
    print('total graph size is')
    print('  nodes:', len(nodes))
    print()
    from pprint import pprint
    pprint(links, width=160)
    return Graph(nodes, links)


def inverse_edges(graph: Graph) -> Graph:
    links: dict[str, list[str]] = {}
    queue = [*graph.nodes]
    while queue:
        src, queue = queue[0], queue[1:]
        for dst in graph.links.get(src, []):
            if dst not in links:
                links[dst] = []
            links[dst].append(src)
    print(links['python-numpy'])
    return Graph([*graph.nodes], links)


def subgraph_of(graph: Graph, origin: str) -> list[list[str]]:
    effects: dict[str, int] = {}
    queue: list[tuple[str, int]] = [(origin, 0)]
    while queue:
        (src, depth), queue = queue[0], queue[1:]
        effects[src] = max(depth, effects.get(src, 0))
        if (links := graph.links.get(src)):
            queue += [(x, depth + 1) for x in links]

    max_depth = max(effects.values())
    gens = [set() for _ in range(max_depth + 1)]
    for k, v in effects.items():
        gens[v].add(k)
    return [sorted(x) for x in gens]
