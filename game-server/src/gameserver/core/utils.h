#pragma once

#include <chrono>

#include "defs.h"

int64 currentMSecsSinceEpoch();

template <typename T> T sgn(T val) {
    return ((val<T(0)) ? (T(-1)) : (T(+1)));
}

template<typename TimeT = std::chrono::milliseconds>
struct measure
{
    template<typename F, typename ...Args>
    static typename TimeT::rep execution(F&& func, Args&&... args)
    {
        auto start = std::chrono::steady_clock::now();
        std::forward<decltype(func)>(func)(std::forward<Args>(args)...);
        auto duration = std::chrono::duration_cast< TimeT> 
                            (std::chrono::steady_clock::now() - start);
        return duration.count();
    }
};

#define TIME_IT(x)  measure<std::chrono::microseconds>::execution([&](){x;})

#ifndef ABS
#define ABS(m_v) ((m_v<0)?(-(m_v)):(m_v))
#endif

#ifndef SGN
#define SGN(m_v) ((m_v<0)?(-1.0):(+1.0))
#endif

#ifndef MIN
#define MIN(m_a,m_b) (((m_a)<(m_b))?(m_a):(m_b))
#endif

#ifndef MAX
#define MAX(m_a,m_b) (((m_a)>(m_b))?(m_a):(m_b))
#endif

#ifndef CLAMP
#define CLAMP(m_a,m_min,m_max) (((m_a)<(m_min))?(m_min):(((m_a)>(m_max))?m_max:m_a))
#endif

std::string hex_md5(const uint8_t *p_md5);
std::string hex_encode_buffer(const uint8_t *p_buffer, int p_len);

void latin_to_utf8(const char* p_str, uint32_t p_str_size, char* p_buffer, uint32_t p_buffer_size);
int utf8_strlen(const char* str, uint str_len);

void get_sunflower_points(uint n, Vector2* points);

void get_random_string(char* dst, uint dst_size);
void get_random_hex_string(char* dst, uint dst_size);
void get_random_bytes(ubyte* dst, uint dst_size);

uint64_t get_ticks_usec();

uint required_bits(uint number);