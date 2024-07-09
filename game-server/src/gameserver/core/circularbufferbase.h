#pragma once

#include "defs.h"

template <typename V>
class CircularBufferBase
{
    using T = typename V::value_type;

public:
    CircularBufferBase()
    {
        _begin = 0;
        _size = 0;
    }

    void pop_front()
    {
        RTCHECK(_size > 0);

        --_size;
        ++_begin;
        _begin = (_begin % capacity());
    }

    void pop_back()
    {
        RTCHECK(_size > 0);

        --_size;
    }

    void push_back(const T& v)
    {
        const uint cap = capacity();
        RTCHECK(_size < cap);

        _buffer[(_begin + _size) % cap] = v;
        ++_size;
    }

    void push_front(const T& v)
    {
        const uint cap = capacity();
        RTCHECK(_size < cap);

        _begin = (_begin + (cap - 1)) % cap;
        _buffer[_begin] = v;
        ++_size;
    }

    const T& back()  const { RTCHECK(_size > 0); return _buffer[(_begin + _size - 1) % capacity()]; }
          T& back()        { RTCHECK(_size > 0); return _buffer[(_begin + _size - 1) % capacity()]; }
    const T& front() const { RTCHECK(_size > 0); return _buffer[_begin]; }
          T& front()       { RTCHECK(_size > 0); return _buffer[_begin]; }

    const T& operator[](uint i) const { RTCHECK(i < _size); return _buffer[(_begin + i) % capacity()]; }
          T& operator[](uint i)       { RTCHECK(i < _size); return _buffer[(_begin + i) % capacity()]; }

    bool empty() const { return (_size == 0); }
    bool full() const { return (_size == capacity()); }
    uint size() const { return _size; }

    uint capacity() const { return (uint)_buffer.size(); }

    void clear() { _begin = 0; _size = 0; }

    void pack() // Mueve el contenido del circular buffer al principio de _buffer, de tal manera que _begin sera 0.
    {
        V new_buffer;
        new_buffer.reserve(capacity());
        new_buffer.resize(_size);
        for (uint i = 0; i < _size; ++i)
        {
            new_buffer[i] = (*this)[i];
        }
        std::copy(new_buffer.begin(), new_buffer.end(), _buffer.begin());
        _begin = 0;
    }

    void set_capacity(uint new_capacity) 
    {
        if (new_capacity != capacity())
        {
            pack();
            _buffer.resize(new_capacity);
            if (_size > capacity())
                _size = capacity();
        }
    }

protected:
    V& get_buffer() { return _buffer; }

private:
    V    _buffer;
    uint _begin;
    uint _size;
};