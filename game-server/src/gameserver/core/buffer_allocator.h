#pragma once

#include <vector>

#include "core/types.h"

class BufferAllocator
{
public:
    BufferAllocator();
    ubyte* allocate(uint buffer_size);
    void free_all();

private:
    std::vector<ubyte> _memory;
    uint               _used;      // Cantidad de memoria usada, en bytes.
};

inline BufferAllocator::BufferAllocator()
{
    _memory.resize(1 << 16);    // 64KB
    _used = 0;
}

inline ubyte* BufferAllocator::allocate(uint buffer_size)
{
    if (buffer_size == 0) return NULL;

    if (_memory.size() < (_used + buffer_size))
    {
        _memory.resize(_memory.size() + buffer_size);
    }

    ubyte* ptr = _memory.data() + _used;

    _used += buffer_size;

    return ptr;
}

inline void BufferAllocator::free_all()
{
    _memory.clear();
    _used = 0;
}
