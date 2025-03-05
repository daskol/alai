find_package(PkgConfig REQUIRED)

pkg_check_modules(ALPM REQUIRED IMPORTED_TARGET GLOBAL libalpm>=15)

message(STATUS "ALPM includes: ${ALPM_INCLUDE_DIRS}")
message(STATUS "ALPM libraries: ${ALPM_LINK_LIBRARIES}")

add_library(alai STATIC)

target_sources(alai
    PUBLIC
        alai.h
    PRIVATE
        alai.cc
)

target_include_directories(alai PUBLIC ${PROJECT_SOURCE_DIR})

target_link_libraries(alai PUBLIC PkgConfig::ALPM)

if (ENABLE_TESTS)
    find_package(GTest REQUIRED)

    add_executable(alai_cc_test alai_test.cc)

    target_link_libraries(alai_cc_test PRIVATE GTest::gtest_main alai)
    target_include_directories(alai_cc_test PRIVATE ${PROJECT_SOURCE_DIR})
endif()
