#pragma once

#include <cinttypes>

typedef unsigned char       ubyte;
typedef unsigned short      ushort;
typedef unsigned int        uint;
typedef long long           int64;
typedef unsigned long long  uint64;
 
struct BytesView
{
    BytesView() : data(0), size(0) {}
    BytesView(const ubyte* d, uint s) : data(d), size(s) {}
    const ubyte* data;
    uint         size;
};