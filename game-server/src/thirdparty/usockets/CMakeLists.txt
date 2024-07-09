# CMakeList.txt: proyecto de CMake para usockets, incluya el origen y defina
# la lógica específica del proyecto aquí.
#
#cmake_minimum_required (VERSION 3.8)

#project ("usockets")

# Agregue un origen al ejecutable de este proyecto.
add_library (usockets 
    "bsd.c"
    "context.c"
    "crypto/openssl.c"
    "crypto/sni_tree.cpp"
    "crypto/wolfssl.c"
    "eventing/asio.cpp"
    "eventing/epoll_kqueue.c"
    "eventing/gcd.c"
    "eventing/libuv.c"
    "internal/eventing/asio.h"
    "internal/eventing/epoll_kqueue.h"
    "internal/eventing/gcd.h"
    "internal/eventing/libuv.h"
    "internal/internal.h"
    "internal/loop_data.h"
    "internal/networking/bsd.h"
    "libusockets.h"
    "loop.c"
    "socket.c"
)

target_compile_definitions(usockets PUBLIC LIBUS_USE_LIBUV LIBUS_USE_OPENSSL)

target_include_directories(usockets PUBLIC ".")

target_compile_options(usockets PUBLIC "-std=c++17" )





