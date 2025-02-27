#!/usr/bin/env bash
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

# Simple script based on `libmakepkg` (see `pacman` sources) in order to obtain
# metadata `PKGBUILD`. A `PKGBUILD` file is essentially a bash script which is
# sourced and executed by `makepkg` script.

print_usage() {
    >&2 echo "usage: $0 <PKGBUILD>"
    exit 1
}

print_pkgbuild() {
    source_safe $1

    pkgbase=${pkgbase:-$pkgname}

    # Print actual schema of `PKGBUILD`.
    declare -p pkgbuild_schema_arrays
    declare -p pkgbuild_schema_strings
    declare -p pkgname

    for varname in ${pkgbuild_schema_arrays[@]}; do
        if declare -p "$varname" > /dev/null 2>&1; then
            declare -p "$varname"
        fi
    done

    for varname in ${pkgbuild_schema_strings[@]}; do
        if declare -p "$varname" > /dev/null 2>&1; then
            declare -p "$varname"
        fi
    done
}

if [ -z "$1" ]; then
    print_usage
fi

MAKEPKG_LIBRARY=${MAKEPKG_LIBRARY:-'/usr/share/makepkg'}
source "$MAKEPKG_LIBRARY/util.sh"
print_pkgbuild $1
