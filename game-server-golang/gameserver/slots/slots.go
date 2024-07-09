package slots

import (
	"github.com/gofiber/websocket/v2"
)

const (
	RegistryOperationAcquireSlot = 0
	RegistryOperationReleaseSlot = 1
)

type Slot struct {
	C                *websocket.Conn // El puntero al websocket asociado a este slot.
	SlotId           int             // El id de este slot.
	IsAssignedToUser bool            // Indica si el slot se ha asignado a un usuario.
	UserId           int             // En caso de que IsAssignedToUser sea true entonces indica el id del user al que se ha asignado el slot.
}

// type Slots struct {
// 	slots        []Slot
// 	freeSlotIds  []int
// 	maxSlotCount int
// }

// func (s *Slots) Initialize(maxSlotCount int) {
// 	s.maxSlotCount = maxSlotCount
// 	s.slots = make([]Slot, maxSlotCount)
// 	s.freeSlotIds = make([]int, maxSlotCount)
// 	for i := 0; i < maxSlotCount; i++ {
// 		s.freeSlotIds[i] = maxSlotCount - i - 1
// 	}
// }

// func (s *Slots) AcquireSlot(sd SlotData) int {
// 	if sd.C == nil {
// 		panic(0)
// 	}

// 	if len(s.freeSlotIds) == 0 {
// 		return -1
// 	} else {
// 		slotId := s.freeSlotIds[len(s.freeSlotIds)-1]
// 		s.freeSlotIds = s.freeSlotIds[:len(s.freeSlotIds)-1]
// 		s.slots[slotId] = Slot{
// 			SlotId:   slotId,
// 			SlotData: sd,
// 		}
// 		return slotId
// 	}
// }

// func (s *Slots) ReleaseSlot(slotId int) {
// 	if len(s.freeSlotIds) < s.maxSlotCount {
// 		if slotId >= 0 && slotId < s.maxSlotCount {
// 			s.slots[slotId] = Slot{}
// 			s.freeSlotIds = append(s.freeSlotIds, slotId)
// 		}
// 	}
// }

// func (s *Slots) UsedSlotCount() int {
// 	return s.maxSlotCount - len(s.freeSlotIds)
// }

// func (s *Slots) GetSlot(slotId int) Slot {
// 	if slotId < 0 || slotId >= s.maxSlotCount {
// 		panic(0)
// 	}
// 	return s.slots[slotId]
// }
