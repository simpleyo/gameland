package entity

type Stateable[T comparable] struct {
	state T
}

func (s *Stateable[T]) GetState() T {
	return s.state
}

func (s *Stateable[T]) HasState(state T) bool {
	return s.state == state
}
