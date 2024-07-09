#pragma once

#include <cinttypes>

// Code relying on a big-endian architecture cannot be compiled by Emscripten.
// Emscripten-compiled code currently requires a little-endian host to run on, 
// which accounts for 99% of machines connected to the internet. This is because 
// JavaScript typed arrays (used for views on memory) obey the host byte ordering 
// and LLVM needs to know which endianness to target.

#define NETWORK_ENDIANNESS E_LITTLE_ENDIAN
#define HOST_ENDIANNESS    E_LITTLE_ENDIAN      

namespace endian
{
    int check_endianness();
    const int host_endianness = check_endianness(); // Comprueba que la endianness real del host (el que ejecuta este codigo) es la indicada por HOST_ENDIANNESS.
        
    enum Endianness {
        E_LITTLE_ENDIAN = 0,
        E_BIG_ENDIAN
    };

    //! Byte swap unsigned short
    inline uint16_t swap_uint16(uint16_t val)
    {
        return (val << 8) | (val >> 8);
    }

    //! Byte swap short
    inline int16_t swap_int16(int16_t val)
    {
        return (val << 8) | ((val >> 8) & 0xFF);
    }

    //! Byte swap unsigned int
    inline uint32_t swap_uint32(uint32_t val)
    {
        val = ((val << 8) & 0xFF00FF00) | ((val >> 8) & 0xFF00FF);
        return (val << 16) | (val >> 16);
    }

    //! Byte swap int
    inline int32_t swap_int32(int32_t val)
    {
        val = ((val << 8) & 0xFF00FF00) | ((val >> 8) & 0xFF00FF);
        return (val << 16) | ((val >> 16) & 0xFFFF);
    }
    
    inline int64_t swap_int64(int64_t val)
    {
        val = ((val << 8) & 0xFF00FF00FF00FF00ULL) | ((val >> 8) & 0x00FF00FF00FF00FFULL);
        val = ((val << 16) & 0xFFFF0000FFFF0000ULL) | ((val >> 16) & 0x0000FFFF0000FFFFULL);
        return (val << 32) | ((val >> 32) & 0xFFFFFFFFULL);
    }

    inline uint64_t swap_uint64(uint64_t val)
    {
        val = ((val << 8) & 0xFF00FF00FF00FF00ULL) | ((val >> 8) & 0x00FF00FF00FF00FFULL);
        val = ((val << 16) & 0xFFFF0000FFFF0000ULL) | ((val >> 16) & 0x0000FFFF0000FFFFULL);
        return (val << 32) | (val >> 32);
    }
}

#if 0 

    // Implementacion para Host != Network

     inline int16_t hton_i16(int16_t v) { return endian::swap_int16(v); }
#define ntoh_i16(v) hton_i16(v)
     inline int32_t hton_i32(int32_t v) { return endian::swap_int32(v); }
#define ntoh_i32(v) hton_i32(v)
     inline int64_t hton_i64(int64_t v) { return endian::swap_int64(v); }
#define ntoh_i64(v) hton_i64(v)
     
       inline uint16_t hton_uint16(uint16_t v) { return endian::swap_uint16(v); }
#define ntoh_uint16(v) hton_uint16(v)
       inline uint32_t hton_uint32(uint32_t v) { return endian::swap_uint32(v); }
#define ntoh_uint32(v) hton_uint32(v)
       inline uint64_t hton_uint64(uint64_t v) { return endian::swap_uint64(v); }
#define ntoh_uint64(v) hton_uint64(v)

#else

    // Implementacion para Host == Network
    
#define hton_i16(v) v
#define ntoh_i16(v) v
#define hton_i32(v) v
#define ntoh_i32(v) v
#define hton_i64(v) v
#define ntoh_i64(v) v

#define hton_u16(v) v
#define ntoh_u16(v) v
#define hton_u32(v) v
#define ntoh_u32(v) v
#define hton_u64(v) v
#define ntoh_u64(v) v

#endif
