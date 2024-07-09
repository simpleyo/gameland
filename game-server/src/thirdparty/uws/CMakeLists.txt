# CMakeList.txt: proyecto de CMake para uws, incluya el origen y defina
# la lógica específica del proyecto aquí.
#
#cmake_minimum_required (VERSION 3.8)

#project ("uws")

# Agregue un origen al ejecutable de este proyecto.
add_library (uws 
    "uWS.h"
    "Libuv.h"
    "WebSocketProtocol.h"

    "Epoll.cpp" 
    "Epoll.h" 
    "Extensions.cpp"
    "Extensions.h"
    "Group.cpp"
    "Group.h"
    "HTTPSocket.cpp"
    "HTTPSocket.h"
    "Hub.cpp"
    "Hub.h"
    "Networking.cpp"
    "Networking.h"
    "Node.cpp"
    "Node.h"
    "Socket.cpp"
    "Socket.h"
    "WebSocket.cpp"
    "WebSocket.h"
)

target_compile_definitions(uws PUBLIC USE_LIBUV)

target_compile_options(uws PUBLIC "-std=c++17" )





