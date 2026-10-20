# yes, this cmakelist was made with ai
# as such it's buggy
# if you know what you're doing i would GREATLY appreciate if you could help
# i don't particularly like using ai for serious projects like this


cmake_minimum_required(VERSION 3.12)
project(neoprisma_playback LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 🌟 FIX 1: Try finding pybind11 using 'python3' first
execute_process(
    COMMAND python3 -c "import pybind11; print(pybind11.get_cmake_dir())"
    OUTPUT_VARIABLE PYBIND11_CMAKE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
)

# 🌟 FIX 2: If 'python3' failed (standard on Windows), gracefully fall back to 'python'
if(NOT PYBIND11_CMAKE_DIR)
    execute_process(
        COMMAND python -c "import pybind11; print(pybind11.get_cmake_dir())"
        OUTPUT_VARIABLE PYBIND11_CMAKE_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
    )
endif()

# Inform CMake of the verified path configuration location
set(pybind11_DIR "${PYBIND11_CMAKE_DIR}")
find_package(pybind11 REQUIRED)

# Define the Python extension module binary layout mapping to src/
pybind11_add_module(playback 
    src/playback.cpp
)
# Force the binary into /src across both single-config and multi-config (Visual Studio) generators
set_target_properties(playback PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/src"
    LIBRARY_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/src"
    LIBRARY_OUTPUT_DIRECTORY_DEBUG "${CMAKE_CURRENT_SOURCE_DIR}/src"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/src"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/src"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_CURRENT_SOURCE_DIR}/src"
)

# Dynamic Platform Architecture & Source Mapping
if(APPLE)
    execute_process(
        COMMAND uname -m
        OUTPUT_VARIABLE HOST_ARCH
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    set(CMAKE_OSX_ARCHITECTURES "${HOST_ARCH}")
    message(STATUS "macOS Target Architecture auto-set to: ${CMAKE_OSX_ARCHITECTURES}")

    target_sources(playback PRIVATE src/automation_macos.cpp)
    target_compile_options(playback PRIVATE -O3 -Wall)
    
    find_library(CORE_GRAPHICS_FRAMEWORK CoreGraphics REQUIRED)
    find_library(APP_SERVICES_FRAMEWORK ApplicationServices REQUIRED)
    target_link_libraries(playback PRIVATE ${CORE_GRAPHICS_FRAMEWORK} ${APP_SERVICES_FRAMEWORK})
    
elseif(WIN32)
    target_sources(playback PRIVATE src/automation_windows.cpp)
    
    # Target Windows multimedia engine dependencies for the timing precision loop fix
    target_link_libraries(playback PRIVATE winmm)
    
    # Optimize compilation by reducing the core Windows header inclusion matrix
    target_compile_definitions(playback PRIVATE WIN32_LEAN_AND_MEAN)
endif()