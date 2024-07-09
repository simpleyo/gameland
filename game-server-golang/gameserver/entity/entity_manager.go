package entity

type EntityManagerOwner interface {
	DestroyEndPhaseEntities()
}

type EntityManager struct {
	EntityManagerOwner
}

func (em *EntityManager) Prepare(prev_delta float64) {
	// em.DestroyEndPhaseEntities()
	// em.EntityManagerOwner.Prepare(prev_delta)
}

func (em *EntityManager) EntityPrepare(ei EntityInterface) {
	e := ei.GetEntity()

	if e.Phase == PHASE_READY {

	}
}
