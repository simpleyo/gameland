#pragma once

#include "defs.h"
#include "endian.h"
#include "logger.h"

int endian::check_endianness()
{
    union {
        uint32_t i;
        uint8_t c[4];
    } bint = { 0x01020304 };

    const int endianness = (bint.c[0] == 1) ? E_BIG_ENDIAN : E_LITTLE_ENDIAN;

    RTCHECK(endianness == HOST_ENDIANNESS);

    return (bint.c[0] == 1);
}


