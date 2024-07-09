#pragma once

#include <vector>

#include "defs.h"

template <typename T>
class DoubleBuffer
{
public:
    DoubleBuffer() : _read_buffer_index(0) {}

    T& get_write_buffer() { return _buffers[!_read_buffer_index]; }
    const T& get_read_buffer() const { return _buffers[_read_buffer_index]; }
    void swap_buffers() { _read_buffer_index = !_read_buffer_index; }

private:
    ubyte           _read_buffer_index;
    T               _buffers[2];

};