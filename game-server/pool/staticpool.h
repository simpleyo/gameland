#pragma once

#include <vector>

#include "core/defs.h"

//
// Pool de capacidad fija. Optimizado para la liberacion rapida de objects.
// La asignacion de objects se realiza indicando el object_id que se desea (por eso se denomina StaticPool, 
// ya que no permite una llamada a alloc sin indicar el object_id). 
// Es posible que el object_id deseado ya este ocupado
// por lo que el proceso de asignacion puede tener un coste lineal con el tamaño de la pool.
// Un object viene determinado por el tipo T. 
// Una vez asignado un object (mediante StaticPool::alloc), el object siempre permanece en la misma posicion de memoria.
//
template <typename T>
class StaticPool      
{
public:
    StaticPool(uint capacity);
    virtual ~StaticPool();

    bool alloc(IDR object_id);
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

    uint get_object_count() const { return _object_count; }

private:
    uint                _capacity;
    T*                  _objects;         // dado un object_id devuelve un T
    std::vector<bool>   _is_allocated;    // dado un object_id devuelve un bool

    uint                _object_count;
};

template<typename T> inline 
StaticPool<T>::StaticPool(uint capacity)
{
    RTCHECK(capacity > 0);
    //_objects.resize(capacity);
    _capacity = capacity;
    _objects = (T*)(::operator new (capacity * sizeof(T)));
    
    clear();
}

template<typename T> inline 
StaticPool<T>::~StaticPool()
{
    (::operator delete (_objects));
}

template<typename T> inline 
void StaticPool<T>::clear()
{
    _is_allocated.clear();
    _is_allocated.resize(_capacity, false);
    _object_count = 0;
}

template<typename T> inline 
bool StaticPool<T>::alloc(IDR object_id)
{
    //RTCHECK(!_free_object_ids.empty());
    //const IDR object_id = _free_object_ids.back();
    //_free_object_ids.pop_back();

    if (!_is_allocated[object_id])
    {
        _is_allocated[object_id] = true;
        ++_object_count;
        return true;
    }
    else
    {
        return false;
    }

    //new (_objects.data() + object_id) T();  // construct T

    //return object_id;
}

template<typename T> inline 
void StaticPool<T>::free(IDR object_id)
{
    RTCHECK(_is_allocated[object_id]);
    _is_allocated[object_id] = false;
    RTCHECK(_object_count > 0);
    --_object_count;

    //RTCHECK(_free_object_ids.size() < _capacity); //_objects.size());
    //RTCHECK(object_id < _capacity); //_objects.size());
    //
    //RTCHECK(_is_allocated[object_id]);

    ////(_objects.data() + object_id)->~T();    // destruct T

    //_is_allocated[object_id] = false;

    //_free_object_ids.push_back(object_id);
}
