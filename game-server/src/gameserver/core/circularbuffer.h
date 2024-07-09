#pragma once

#include <vector>

#include "circularbufferbase.h"

template <typename T>
class CircularBuffer : public CircularBufferBase<std::vector<T>>
{
    using Base = CircularBufferBase<std::vector<T>>;

public:
    CircularBuffer() : Base() {}
    
    CircularBuffer(uint capacity)
    {
        RTCHECK(capacity > 0);
        Base::get_buffer().resize(capacity);
    }

    void construct(uint capacity)
    {
        RTCHECK(get_buffer().empty());
        RTCHECK(capacity > 0);
        Base::get_buffer().resize(capacity);
    }

    using Base::get_buffer;
};