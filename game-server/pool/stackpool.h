#pragma once

#include <vector>

#include "core/defs.h"

//
// Pool de capacidad fija. Optimizado para la adicion y eliminacion rapida de objetos.
// Los elementos siempre se insertan o eliminan en final de la pool, es decir, los elementos
// siempre se eliminan en orden inverso a su insercion.
// Una vez asignado un object_id a un objeto, este siempre permanece en la misma posicion de memoria y con el mismo
// object_id hasta que es removido de la pool.
// Objetos con object_id consecutivos no se garantiza que esten en posiciones consecutivas de memoria.
// La iteracion de los objetos se realiza de manera directa mediante get_object_count y get_data o get_object.
// La lista de objetos devueltos por get_objects_list esta ordenada por object_id.
// Para iterar sobre los elementos:
//     - usar get_objects_list() para obtener el array de object ids
//     - iterar sobre ese array y utilizar get_object para acceder a los objetos.
//
template <typename T>
class StackPool    
{
public:
    static const uint INVALID_INDEX = UINT_MAX;

public:
    StackPool(uint capacity);
    virtual ~StackPool();

    uint  get_capacity() const { return _capacity; }
    uint  get_object_count() const { return _object_count; }

    void clear();

    IDR  alloc_back(); // Asigna IDR de forma incremental. Empieza en 0 y termina en _capacity-1.
    bool free_back(); // Liberar el ultimo elemento que fue insertado.
    IDR back(); // Obtiene el id del ultimo elemento que fue insertado.

    bool is_valid(IDR object_id) const { return (object_id < _object_count); }

          T* get_object_ptr(IDR object_id)       { RTCHECK(is_valid(object_id)); return _objects + object_id; }
    const T* get_object_ptr(IDR object_id) const { RTCHECK(is_valid(object_id)); return _objects + object_id; }

          T& get_object(IDR object_id)       { RTCHECK(is_valid(object_id)); return _objects[object_id]; }
    const T& get_object(IDR object_id) const { RTCHECK(is_valid(object_id)); return _objects[object_id]; }
    
          T* get_data()       { return _objects; }
    const T* get_data() const { return _objects; }

private:

    uint                _capacity;    
    uint                _object_count;
    T*                  _objects;                // para un object_id devuelve un T
};

template<typename T> inline 
StackPool<T>::StackPool(uint capacity) :
    _capacity(capacity)
{
    RTCHECK(capacity > 0);

    _objects = (T*)(::operator new (_capacity * sizeof(T)));

    _object_count = 0;
}

template<typename T> inline 
StackPool<T>::~StackPool()
{
    (::operator delete (_objects));
}

template<typename T> inline 
void StackPool<T>::clear()
{
    _object_count = 0;
}

template<typename T> inline 
IDR StackPool<T>::alloc_back()
{
    IDR new_object_id;

    if (_object_count < _capacity)
    {
        new_object_id = _object_count;
        ++_object_count;
    }

    return new_object_id;
}

template<typename T> inline 
bool StackPool<T>::free_back()
{
    bool result = false;

    if (_object_count > 0)
    {
        --_object_count;
        result = true;
    }

    return result;
}

template<typename T> inline 
IDR StackPool<T>::back()
{
    IDR object_id;

    if (_object_count > 0)
    {
        object_id = _object_count-1;
    }

    return object_id;
}
