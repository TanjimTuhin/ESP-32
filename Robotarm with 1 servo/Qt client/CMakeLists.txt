find_package(Qt6 REQUIRED COMPONENTS Gui)
find_package(Qt6 REQUIRED COMPONENTS Gui Network)

qt_add_library(backendmodule STATIC)

qt_add_qml_module(backendmodule
    URI Backend
    VERSION 1.0
    SOURCES
        animatedparam.cpp
        animatedparam.h
        backend.cpp
        backend.h
        esp32client.h
        esp32client.cpp
    RESOURCE_PREFIX "/"
)

target_link_libraries(backendmodule PUBLIC Qt6::Gui)
target_link_libraries(backendmodule PUBLIC Qt6::Gui Qt6::Network)
