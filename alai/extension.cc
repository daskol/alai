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

#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>

#include <alai/cc/alai.h>

namespace nb = nanobind;

namespace {

NB_MODULE(extension, m) {
    using alai::Package;
    nb::class_<Package>(m, "Package")
        .def_ro("name", &Package::name)
        .def_ro("depends", &Package::depends);

    m.def("find_package", alai::FindPackage);
}

} // namespace
