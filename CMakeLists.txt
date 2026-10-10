# yes i used ai to make the cmake sorry
# don't expect it to work well because of that

cmake_minimum_required(VERSION 3.12)
project(neoprisma_playback LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 🌟 AUTOMATED FIX: Ask Python exactly where pybind11's CMake folder is hidden
execute_process(
    COMMAND python3 -c "import pybind11; print(pybind11.get_cmake_dir())"
    OUTPUT_VARIABLE PYBIND11_CMAKE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
# Inform CMake of the hidden pip configuration directory path
set(pybind11_DIR "${PYBIND11_CMAKE_DIR}")

# This will now pass flawlessly without any manual intervention!
find_package(pybind11 REQUIRED)

# 2. Define the Python extension module binary layout mapping to src/
pybind11_add_module(playback 
    src/playback.cpp
)

# Force the binary into /src
set_target_properties(playback PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/src"
)

# 3. Dynamic Platform Architecture & Source Mapping
if(APPLE)
    # Automatically detect the host processor type (arm64 vs x86_64)
    execute_process(
        COMMAND uname -m
        OUTPUT_VARIABLE HOST_ARCH
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    set(CMAKE_OSX_ARCHITECTURES "${HOST_ARCH}")
    message(STATUS "macOS Target Architecture auto-set to: ${CMAKE_OSX_ARCHITECTURES}")

    # Inject your macOS-specific automation backend file
    target_sources(playback PRIVATE src/automation_macos.cpp)
    
    # Performance Optimization flags
    target_compile_options(playback PRIVATE -O3 -Wall)
    
    # Target system Framework dependencies natively used by your macOS automation hook
    find_library(CORE_GRAPHICS_FRAMEWORK CoreGraphics REQUIRED)
    find_library(APP_SERVICES_FRAMEWORK ApplicationServices REQUIRED)
    target_link_libraries(playback PRIVATE ${CORE_GRAPHICS_FRAMEWORK} ${APP_SERVICES_FRAMEWORK})
    
elseif(WIN32)
    # Inject your Windows-specific automation backend file
    target_sources(playback PRIVATE src/automation_windows.cpp)
    
    # Target Windows multimedia engine dependencies for the timing precision loop fix
    target_link_libraries(playback PRIVATE winmm)
    
    # Optimize compilation by reducing the core Windows header inclusion matrix
    target_compile_definitions(playback PRIVATE WIN32_LEAN_AND_MEAN)
endif()
