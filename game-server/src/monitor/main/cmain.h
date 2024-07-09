#pragma once

#include "core/types.h"

class Main
{
public:
    static void configure(int argc, char **argv);
    static void setup();
    static bool initialize(); // Retorna true si esta todo correcto.
    static void run();
    static bool iteration(); // Si retorna true entonces el loop termina.
    static void finalize();     
    static void cleanup();

    static uint IPS();
    static uint UPS();
};