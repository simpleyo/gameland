#pragma once

#include <vector>
#include <climits>

#include "core/defs.h"

//
// Pool de capacidad fija. Optimizado para la adicion y eliminacion rapida de objetos.
// Una vez asignado un object_id a un objeto, este siempre permanece en la misma posicion de memoria y con el mismo
// object_id hasta que es removido de la pool.
// Objetos con object_id consecutivos no se garantiza que esten en posiciones consecutivas de memoria.
// La iteracion de los objetos se realiza de manera indirecta mediante get_objects_list.
// ATENCION: La lista de objetos devueltos por get_objects_list no tiene por que estar ordenada por object_id.
//           Solo se garantiza que estaran ordenados, por object_id, si, y solo si, todas las llamadas
//           a free se producen en orden inverso a las correspondientes llamadas a alloc, es decir, las llamadas a free
//           siempre deben tener como parametro el mayor object_id que hay en ese momento en el ObjectPool.
// Para iterar sobre los elementos:
//     - usar get_objects_list() para obtener el array de object ids
//     - iterar sobre ese array y utilizar get_object para acceder a los objetos.
//
template <typename T>
class ObjectPool    
{
public:
    static const int INVALID_INDEX = 0xFFFFFFFF;

public:
    ObjectPool(uint capacity);
    virtual ~ObjectPool();

    uint  get_capacity() const { return _capacity; }
    uint  get_object_count() const { return (uint)_objects_list.size(); }

    bool empty() const { return !_objects_list.size(); }
    bool full() const { return (get_object_count() == _capacity); }

    void clear();

    IDR alloc(); // Asigna IDR de forma incremental mientras sea posible. Empieza en 0 y termina en _capacity-1.
    bool free(IDR object_id);   // Liberar el object especificado.

    bool is_valid(IDR object_id) const { return (object_id < _capacity) && (_index[object_id] != INVALID_INDEX); }

          T* get_object_ptr(IDR object_id)       { RTCHECK(is_valid(object_id)); return _objects + object_id; }
    const T* get_object_ptr(IDR object_id) const { RTCHECK(is_valid(object_id)); return _objects + object_id; }

          T& get_object(IDR object_id)       { RTCHECK(is_valid(object_id)); return _objects[object_id]; }
    const T& get_object(IDR object_id) const { RTCHECK(is_valid(object_id)); return _objects[object_id]; }
    
    uint get_object_index(IDR object_id) const { RTCHECK(object_id < _capacity); return _index[object_id]; }

          T& get_object_by_index(uint index)       { RTCHECK(index < _objects_list.size()); return _objects[_objects_list[index]]; }
    const T& get_object_by_index(uint index) const { RTCHECK(index < _objects_list.size()); return _objects[_objects_list[index]]; }

          T* get_data()       { return _objects; }
    const T* get_data() const { return _objects; }
    
    const std::vector<IDR>& get_objects_list() const { return _objects_list; }

private:

    uint                _capacity;
                                                    
    std::vector<uint>   _index;                  // para un object_id devuelve un indice en _objects_list
    T*                  _objects;                // para un object_id devuelve un T

    std::vector<IDR>   _objects_list;           // para un indice devuelve un object_id
    
    std::vector<IDR>   _free_object_ids;        // dado un indice devuelve un object_id que no esta siendo usado

};

template<typename T> inline 
ObjectPool<T>::ObjectPool(uint capacity) :
    _capacity(capacity)
{
    RTCHECK(capacity > 0);

    _index.resize(_capacity, INVALID_INDEX);
    _objects = (T*)(::operator new (_capacity * sizeof(T)));
    RTCHECK(_objects != 0);
    //_objects.resize (_capacity);
    _free_object_ids.resize(_capacity);

    clear();
}

template<typename T> inline 
ObjectPool<T>::~ObjectPool()
{
    (::operator delete (_objects));
}

template<typename T> inline 
void ObjectPool<T>::clear()
{
    _index.clear();
    _index.resize(_capacity, INVALID_INDEX);
    _objects_list.clear();

    _free_object_ids.clear();
    _free_object_ids.resize(_capacity);
    const int ei = (int)_free_object_ids.size();
    for (int i=0; i<ei; ++i)
    {
        _free_object_ids[i] = (ei-1) - i;
    }

    //RTCHECK(_objects.size() == _capacity);
    RTCHECK(_index.size() == _capacity);
    RTCHECK(_free_object_ids.size() == _capacity);
}

template<typename T> inline 
IDR ObjectPool<T>::alloc()
{
    IDR new_object_id;

    if (!_free_object_ids.empty())
    {
        new_object_id = _free_object_ids.back();
        _free_object_ids.pop_back();

        const uint object_count = (uint)_objects_list.size();
        _index[new_object_id] = object_count;

        _objects_list.push_back(new_object_id);

        RTCHECK((_objects_list.size() + _free_object_ids.size()) == _capacity); //_objects.capacity());
    }

    return new_object_id;
}

template<typename T> inline 
bool ObjectPool<T>::free(IDR object_id)
{
    RTCHECK(object_id < _capacity);
            
    bool result = false;

    const uint objects_count = (uint)_objects_list.size();
    if (objects_count > 0)
    {
        const uint index_a = _index[object_id];
        if (index_a != INVALID_INDEX)
        {
            _free_object_ids.push_back(object_id);

            if (index_a < (objects_count-1))
            {
                const IDR m_id  = _objects_list[objects_count-1];
                
                _objects_list[index_a] = m_id;                                
                _index[m_id] = index_a;
            }

            _index[object_id] = INVALID_INDEX;

            _objects_list.pop_back();

            result = true;

            RTCHECK((_objects_list.size() + _free_object_ids.size()) == _capacity); //_objects.capacity());
        }
    }

    return result;
}
