package entity

const (
	PHASE_BEGIN uint8 = iota
	PHASE_READY
	PHASE_END
)

type IDR uint32

func (id IDR) isValid() bool {
	return uint32(id) != ^uint32(0)
}

func (id *IDR) invalidate() {
	*id = IDR(^uint32(0))
}

type EntityOwner interface {
	OnMarkedToBeDeleted()
}

type Entity struct {
	Id      IDR
	Phase   uint8
	Changes uint8
	Flags   uint8
	EntityOwner
}

func MakeEntity(id IDR) *Entity {
	e := Entity{
		Id:    id,
		Phase: PHASE_BEGIN,
	}
	return &e
}

func (e *Entity) InitEntity(id IDR) {
	e.Id = id
	e.Phase = PHASE_BEGIN
}

func (e *Entity) MarkToBeDeleted() {
	e.EntityOwner.OnMarkedToBeDeleted()
}

type EntityInterface interface {
	GetEntity() *Entity
	OnMarkedToBeDeleted()
}
