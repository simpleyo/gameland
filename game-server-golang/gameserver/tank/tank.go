package tank

import (
	"fmt"
	"gameserver-go/entity"
)

type TankSnapData struct {
	entity.Stateable[uint8]
}

type Tank struct {
	entity.Entity
	S Snaps[TankSnapData]
}

func (t *Tank) OnMarkedToBeDeleted() {
	fmt.Println("Tank.OnMarkedToBeDeleted")
}

type TankManager struct {
	entity.EntityManager
}

// Contiene 3 instantaneas (snaps) que representan los estados [Prev, Current, Next]
// Desde el punto de vista del usuario, los snaps Prev y Cur son de solo lectura
// mientras que el snap Next se puede modificar.
// El usuario debe indicar (llamando a NextChanged) si Next ha sido modificado.
type Snaps[T any] struct {
	sb                  [3]T // Snaps buffer
	stepId              uint64
	nextChanged         bool // Indica si Next ha sido modificado.
	notEqualPrevCurrent bool
}

func (s *Snaps[T]) Init(data *T) {
	s.sb[0] = *data
	s.sb[1] = *data
	s.sb[2] = *data
	s.stepId = 0
	s.nextChanged = false
	s.notEqualPrevCurrent = false
}

func (s *Snaps[T]) Prev() *T {
	return &s.sb[0]
}
func (s *Snaps[T]) Curr() *T {
	return &s.sb[1]
}
func (s *Snaps[T]) Next() *T {
	return &s.sb[2]
}

func (s *Snaps[T]) NextChanged() {
	s.nextChanged = true
}

// Advance avanza los snaps hasta el engineStepId indicado.
// <engineStepId> indica el step del engine hasta el que se quiere avanzar.
//
// La funcion Advance es la encargada de mover los snaps hacia la izquierda, es decir:
//		 0   1   2        0   1   2
//		 |   |   |        |   |   |
//		 |   |   |        |   |   |
//		 V   V   V        V   V   V
// 		[P,  C,  N] ---> [C,  N,  N], donde P, C, N, son los valores antes de la llamada a Push.
//
// Esta funcion solo se deberia llamar, como mucho, una vez por step del engine y por objeto dueño de los snaps.
//
func (s *Snaps[T]) Advance(engineStepId uint64) {
	if engineStepId <= s.stepId {
		panic(0)
	}

	d := engineStepId - s.stepId

	if d == 1 {
		if s.nextChanged { // Eso implica que C != N, por lo tanto, despues de las asignaciones (P <- C, C <- N), se cumplira que P != C
			s.sb[0] = s.sb[1] // P <- C
			s.sb[1] = s.sb[2] // C <- N
			s.nextChanged = false
			s.notEqualPrevCurrent = true
		} else { // C == N
			s.sb[0] = s.sb[1] // P <- C
			s.notEqualPrevCurrent = false
		}
	} else { // d >= 2
		if s.notEqualPrevCurrent { // P != C
			s.sb[0] = s.sb[2]  // P <- N
			if s.nextChanged { // C != N
				s.sb[1] = s.sb[2] // C <- N
				s.nextChanged = false
			}
			s.notEqualPrevCurrent = false
		} else { // P == C
			if s.nextChanged { // C != N
				s.sb[0] = s.sb[2] // P <- N
				s.sb[1] = s.sb[2] // C <- N
				s.nextChanged = false
			}
		}
	}
}
