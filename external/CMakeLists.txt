include(FetchContent)

#
# tls::robin-map -- nanobind.

FetchContent_Declare(robin-map
  URL      https://github.com/tessil/robin-map/archive/refs/tags/v1.3.0.tar.gz
  URL_HASH
    SHA256=a8424ad3b0affd4c57ed26f0f3d8a29604f0e1f2ef2089f497f614b1c94c7236
)

#
# Nanobind -- Python extension.

set(NB_USE_SUBMODULE_DEPS OFF)

FetchContent_Declare(nanobind
  URL      https://github.com/wjakob/nanobind/archive/refs/tags/v2.5.0.tar.gz
  URL_HASH
    SHA256=acb2e1997c44f2c79f510c66e7ff9f4cac0502e9fe275ebc7af7571e869f8df0
)

FetchContent_MakeAvailable(robin-map nanobind)
