cmake_minimum_required(VERSION 3.31)

project(alai VERSION 0.0.0 LANGUAGES CXX)

option(ENABLE_TESTS "Build tests or not." OFF)

set(CMAKE_CONFIGURATION_TYPES "Debug;MinSize;Release;RelWithDebInfo" CACHE
    STRING "Available build configurations" FORCE)

message(STATUS "Available build configurations: ${CMAKE_CONFIGURATION_TYPES}")

set(CMAKE_COLOR_DIAGNOSTICS ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED TRUE)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(Python 3.12 REQUIRED COMPONENTS  Interpreter Development.Module)

include(FetchContent)

# For some reason, nanobind fails to attach Python include directories.
include_directories(SYSTEM "${Python_INCLUDE_DIRS}")
include_directories("${FETCHCONTENT_BASE_DIR}/robin-map-src/include")
include_directories("${FETCHCONTENT_BASE_DIR}/nanobind-src/include")

# NOTE Order is important.
add_subdirectory(external)  # Third-party dependencies.

add_subdirectory(alai)
