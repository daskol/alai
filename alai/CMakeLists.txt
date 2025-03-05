add_subdirectory(cc)

find_package(Python 3.12 COMPONENTS Interpreter Development.Module REQUIRED)

nanobind_add_module(extension NOMINSIZE extension.cc)

target_include_directories(extension PRIVATE ${PROJECT_SOURCE_DIR})

target_link_libraries(extension PRIVATE alai)

nanobind_add_stub(extension_stub
    MODULE extension
    OUTPUT extension.pyi
    PYTHON_PATH $<TARGET_FILE_DIR:extension>
    DEPENDS extension
    EXCLUDE_FROM_ALL
)
