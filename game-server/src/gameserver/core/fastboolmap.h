#pragma once

#include <vector>

#include "defs.h"

class FastBoolMap 
{
public:
    FastBoolMap() {}
    FastBoolMap(uint capacity) { construct(capacity); }

    // Para usar despues de FastBoolMap()
    void construct(uint capacity) { _initialize(capacity); }

    template <bool v>
    void set_active(uint index) {} // Coste O(1)

    bool is_active(uint index) const { return (_data[index] == _key); } // Coste O(1)
    bool operator[](uint index) const { return is_active(index); } // Coste O(1)

    // Se fuerza la inicializacion (con coste O(_data.capacity)) una vez cada 2^32 veces. 
    // Todas las demas veces el coste de clear es de O(1)
    void clear() { ++_key; if (!_key) { _initialize((uint)_data.capacity()); } }    
    
    uint capacity() const { return (uint)_data.size(); }

private:
    void _initialize(uint capacity) { _key = 0; _data.clear(); _data.resize(capacity, _key-1); } // Coste O(capacity)

private:
    std::vector<uint>   _data;
    uint                _key;
};

template <> inline
void FastBoolMap::set_active<false>(uint index) { _data[index] = 0; }

template <> inline
void FastBoolMap::set_active<true>(uint index) { _data[index] = _key; }
