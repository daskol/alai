// Copyright 2025 ArchLinux AI
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "alai.h"

#include <print>
#include <string_view>

#include <alpm.h>
#include <alpm_list.h>

using std::operator""sv;

static constexpr std::string_view RootDir = "/"sv;
static constexpr std::string_view DBPath =
    "/var/lib/pacman/"sv; // TODO(@daskol): pacman-conf DBPath

namespace alai {

struct ALPM {
private:
    alpm_handle_t *handle = nullptr;

private:
    ALPM(alpm_handle_t *handle) noexcept : handle{handle} {
    }

public:
    ALPM(void) = default;
    ALPM(ALPM const &) = delete;

    ALPM(ALPM &&that) noexcept {
        std::swap(handle, that.handle);
    }

    ALPM &operator=(ALPM const &) = delete;

    ALPM &operator=(ALPM &&that) noexcept {
        std::swap(handle, that.handle);
        return *this;
    }

public:
    ~ALPM(void) {
        if (handle) {
            alpm_release(handle);
            handle = nullptr;
        }
    }

    operator alpm_handle_t *(void) noexcept {
        return handle;
    }

    static std::optional<ALPM> Initialize(void) {
        alpm_errno_t err;
        alpm_handle_t *handle =
            alpm_initialize(RootDir.data(), DBPath.data(), &err);
        if (!handle) {
            std::println(stderr, "E: failed to initialize alpm: {}",
                         alpm_strerror(err));
            return std::nullopt; // TODO(@daskol): Proper error handling.
        }
        auto alpm = ALPM(handle);
        return std::move(alpm);
    }
};

std::optional<Package> FindPackage(std::string const &name) {
    ALPM alpm;
    if (auto res = ALPM::Initialize()) {
        alpm = std::move(*res);
    } else {
        return std::nullopt;
    }

    constexpr auto level = static_cast<alpm_siglevel_t>(
        ALPM_SIG_DATABASE | ALPM_SIG_DATABASE_OPTIONAL);
    alpm_db_t *db;
    db = alpm_register_syncdb(alpm, "core", level);
    alpm_db_set_usage(db, ALPM_DB_USAGE_ALL);
    db = alpm_register_syncdb(alpm, "extra", level);
    alpm_db_set_usage(db, ALPM_DB_USAGE_ALL);

    auto dbs = alpm_get_syncdbs(alpm);
    auto num_dbs = alpm_list_count(dbs);

    auto pkg = alpm_find_dbs_satisfier(alpm, dbs, name.data());
    if (!pkg) {
        std::println(stderr, "no package");
        return std::nullopt;
    }

    auto depends_list = alpm_pkg_get_depends(pkg);
    std::vector<std::string> depends;
    depends.reserve(alpm_list_count(depends_list));
    for (auto it = depends_list; it != nullptr; it = alpm_list_next(it)) {
        auto dep = reinterpret_cast<alpm_depend_t *>(it->data);
        depends.emplace_back(alpm_dep_compute_string(dep));
    }

    return Package{
        .name = alpm_pkg_get_name(pkg),
        .depends = std::move(depends),
    };
}

} // namespace alai
