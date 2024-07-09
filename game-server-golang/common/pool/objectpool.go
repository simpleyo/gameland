package pool

// ATENCION: Es responsabilidad del usuario de ObjectPool construir y destruir
// los objetos asignados mediante Alloc y liberados mediante Free.
// El usuario no debe asumir que los objetos asignados mediante Alloc estan inicializados a zero-values.
type ObjectPool[T any] struct {
	capacity      int
	objects       []T   // para un object_id devuelve un T
	index         []int // para un object_id devuelve un indice en _objects_list
	objectsList   []int // para un indice devuelve un object_id
	freeObjectIds []int // dado un indice devuelve un object_id que no esta siendo usado
}

const INVALID_INDEX = -1
const INVALID_ID = -1

// Make crea los recursos necesarios para usar esta instancia.
func (s *ObjectPool[T]) Make(capacity int) {
	if capacity <= 0 {
		panic(0)
	}
	s.capacity = capacity
	s.objects = make([]T, capacity)
	s.index = make([]int, capacity)
	s.objectsList = make([]int, 0, capacity)
	s.freeObjectIds = make([]int, capacity)
	for i := 0; i < capacity; i++ {
		s.freeObjectIds[i] = int(capacity - i - 1)
		s.index[i] = -1
	}
}

// Destroy convierte esta instancia en el zero value del tipo ObjectPool[T] liberando todos los recursos.
func (s *ObjectPool[T]) Destroy() {
	*s = ObjectPool[T]{}
}

func (s *ObjectPool[T]) Alloc() int {
	if len(s.freeObjectIds) > 0 {
		newObjectId := s.freeObjectIds[len(s.freeObjectIds)-1]
		s.freeObjectIds = s.freeObjectIds[:len(s.freeObjectIds)-1]
		s.index[newObjectId] = len(s.objectsList)
		s.objectsList = append(s.objectsList, newObjectId)
		if len(s.objectsList)+len(s.freeObjectIds) != s.capacity {
			panic(0)
		}

		// var zero_value T
		// s.objects[newObjectId] = zero_value

		return newObjectId
	} else {
		return INVALID_ID
	}
}

func (s *ObjectPool[T]) Free(objectId int) {
	if len(s.freeObjectIds) < s.capacity {
		if objectId >= 0 && objectId < s.capacity {
			objectsCount := len(s.objectsList)
			if objectsCount > 0 {
				indexA := s.index[objectId]
				if indexA != INVALID_INDEX {
					// var zero_value T
					// s.objects[objectId] = zero_value
					s.freeObjectIds = append(s.freeObjectIds, objectId)

					if indexA < (objectsCount - 1) {
						mId := s.objectsList[objectsCount-1]
						s.objectsList[indexA] = mId
						s.index[mId] = indexA
					}

					s.index[objectId] = INVALID_INDEX
					s.objectsList = s.objectsList[:len(s.objectsList)-1]
					if len(s.objectsList)+len(s.freeObjectIds) != s.capacity {
						panic(0)
					}
				}
			}
		}
	}
}

func (s *ObjectPool[T]) Clear() {
	if s.capacity <= 0 {
		panic(0)
	}

	s.objectsList = s.objectsList[:0]

	// var zero_value T

	for i := 0; i < s.capacity; i++ {
		s.freeObjectIds[i] = int(s.capacity - i - 1)
		s.index[i] = INVALID_INDEX
		// s.objects[i] = zero_value
	}
}

func (s *ObjectPool[T]) Empty() bool {
	return len(s.objectsList) == 0
}

func (s *ObjectPool[T]) Full() bool {
	return len(s.freeObjectIds) == 0
}

func (s *ObjectPool[T]) IsValidObject(objectId int) bool {
	return (objectId >= 0) && (objectId < s.capacity) && (s.index[objectId] != INVALID_INDEX)
}

func (s *ObjectPool[T]) GetObject(objectId int) *T {
	if !s.IsValidObject(objectId) {
		panic(0)
	}
	return &s.objects[objectId]
}

func (s *ObjectPool[T]) GetObjectByIndex(index int) *T {
	if index < 0 || index >= len(s.objectsList) {
		panic(0)
	}
	return &s.objects[s.objectsList[index]]
}

func (s *ObjectPool[T]) GetObjectCount() int {
	return len(s.objectsList)
}

func (s *ObjectPool[T]) Capacity() int {
	return s.capacity
}
