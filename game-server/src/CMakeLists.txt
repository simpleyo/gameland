# CMakeList.txt: proyecto de CMake para src, incluya el origen y defina
# la lógica específica del proyecto aquí.
#
cmake_minimum_required (VERSION 3.8)

project ("gameserver")

add_subdirectory( thirdparty )
add_subdirectory( gameserver )

