#pragma once

#include <vector>

#include "core/defs.h"

//
// Pool de capacidad fija. Optimizado para la asignacion y liberacion rapida de objects.
// Un object viene determinado por el tipo T. 
// Una vez asignado un object (mediante NonIterableObjectPool::alloc), el object siempre permanece en la misma posicion de memoria.
//
template <typename T>
class NonIterableObjectPool      
{
public:
    NonIterableObjectPool(uint capacity);
    virtual ~NonIterableObjectPool();

    IDR alloc();
    void free(IDR object_id);

    bool is_valid(IDR object_id) const { return ((object_id < _capacity) && (_is_allocated[object_id])); }

          T* get_object_ptr(IDR object_id)       { RTCHECK(is_valid(object_id)); return _objects + object_id; }
    const T* get_object_ptr(IDR object_id) const { RTCHECK(is_valid(object_id)); return _objects + object_id; }

          T& get_object(IDR object_id)       { RTCHECK(is_valid(object_id)); return _objects[object_id]; }
    const T& get_object(IDR object_id) const { RTCHECK(is_valid(object_id)); return _objects[object_id]; }

    void clear();

          T* get_data()       { return _objects; }
    const T* get_data() const { return _objects; }

    uint get_capacity() const { return _capacity; }

    uint get_allocated_objects_count() const { return uint(_free_object_ids.capacity() - _free_object_ids.size()); }

private:
    uint                _capacity;
    T*                  _objects;         // dado un object_id devuelve un T
    std::vector<bool>   _is_allocated;    // dado un object_id devuelve un bool

    std::vector<IDR>   _free_object_ids; // dado un indice devuelve un object_id que esta libre

};

template<typename T> inline 
NonIterableObjectPool<T>::NonIterableObjectPool(uint capacity)
{
    RTCHECK(capacity > 0);
    _capacity = capacity;
    _objects = (T*)(::operator new (capacity * sizeof(T)));
    _is_allocated.resize(capacity, false);
    _free_object_ids.resize(capacity);
    
    clear();
}

template<typename T> inline 
NonIterableObjectPool<T>::~NonIterableObjectPool()
{
    (::operator delete (_objects));
}

template<typename T> inline 
void NonIterableObjectPool<T>::clear()
{
    _free_object_ids.clear();
    _free_object_ids.resize(_capacity);
    const int ei = (int)_free_object_ids.size();
    for (int i=0; i<ei; ++i)
    {
        _free_object_ids[i] = (ei-1) - i;
        _is_allocated[i] = false;
    }
}

template<typename T> inline 
IDR NonIterableObjectPool<T>::alloc()
{
    if(_free_object_ids.empty()) return IDR();

    const IDR object_id = _free_object_ids.back();
    _free_object_ids.pop_back();

    RTCHECK(!_is_allocated[object_id]);
    _is_allocated[object_id] = true;

    //new (_objects.data() + object_id) T();  // construct T

    return object_id;
}

template<typename T> inline 
void NonIterableObjectPool<T>::free(IDR object_id)
{
    RTCHECK(_free_object_ids.size() < _capacity); //_objects.size());
    RTCHECK(object_id < _capacity); //_objects.size());
    
    RTCHECK(_is_allocated[object_id]);

    //(_objects.data() + object_id)->~T();    // destruct T

    _is_allocated[object_id] = false;

    _free_object_ids.push_back(object_id);
}
