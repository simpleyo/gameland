package engine

import (
	"common/pool"
	"fmt"
	"time"
)

var eng Engine

const (
	ENGINE_DELTA = time.Millisecond * 50
)

type Engine struct {
	config    Config
	gmaps     pool.ObjectPool[GMap]
	inEvents  chan InEvent
	outEvents chan<- OutEvent
	stepId    int64
	// zeroStepTime time.Time // Tiempo asignado al step[0]. El tiempo teorico para los demas steps es step[stepId] = zeroStepTime + (stepId * ENGINE_DELTA).
}

type Config struct {
	MAX_NUMBER_OF_GMAPS int
	MAX_NUMBER_OF_VIEWS int
}

type GMap struct {
	gmapId int
	roomId int
	views  pool.ObjectPool[View]
}

type View struct {
	viewId        int
	gmapId        int
	playSessionId int
}

// Input event types
const (
	IE_CREATE_GMAP_REQUESTED = iota // Indica al engine que se necesita crear un nuevo GMap.
	IE_CREATE_VIEW_REQUESTED
)

type InEvent struct {
	T             int // El tipo de InEvent.
	RoomId        int
	GMapId        int
	PlaySessionId int
}

// Output event types
const (
	OE_GMAP_CREATED = iota // Indica al game server que se ha creado un nuevo GMap.
	OE_VIEW_CREATED
)

type OutEvent struct {
	T             int // El tipo de OutEvent.
	GMapId        int
	RoomId        int
	ViewId        int
	PlaySessionId int
}

func Initialize(config Config, outEvents chan<- OutEvent) {
	eng.config = config
	eng.outEvents = outEvents
	eng.gmaps.Make(config.MAX_NUMBER_OF_GMAPS)

	eng.inEvents = make(chan InEvent, 1024)
}

func Loop() {
	ticker := time.NewTicker(ENGINE_DELTA)
	lastStepTime := time.Now()
	eng.stepId = 0

	for {
		select {
		case e := <-eng.inEvents:
			if e.T == IE_CREATE_GMAP_REQUESTED {
				doCreateGMap(e.RoomId)
			} else if e.T == IE_CREATE_VIEW_REQUESTED {
				doCreateView(e.GMapId, e.PlaySessionId)
			}
		case t := <-ticker.C:
			if false {
				fmt.Println("Step[", eng.stepId, "]: ", t.Sub(lastStepTime))
			}
			eng.stepId += 1
			lastStepTime = t
		}
	}
}

func CreateGMap(roomId int) {
	eng.inEvents <- InEvent{
		T:      IE_CREATE_GMAP_REQUESTED,
		RoomId: roomId,
	}
}

func CreateView(gmapId int, playSessionId int) {
	eng.inEvents <- InEvent{
		T:             IE_CREATE_VIEW_REQUESTED,
		GMapId:        gmapId,
		PlaySessionId: playSessionId,
	}
}

func doCreateGMap(roomId int) {
	if gmapId := eng.gmaps.Alloc(); gmapId >= 0 {
		m := eng.gmaps.GetObject(gmapId)
		*m = GMap{
			gmapId: gmapId,
			roomId: roomId,
		}
		m.views.Make(eng.config.MAX_NUMBER_OF_VIEWS)

		eng.outEvents <- OutEvent{
			T:      OE_GMAP_CREATED,
			GMapId: gmapId,
			RoomId: roomId,
		}
	}
}

func doCreateView(gmapId int, playSessionId int) {
	m := eng.gmaps.GetObject(gmapId)
	if viewId := m.views.Alloc(); viewId >= 0 {
		v := m.views.GetObject(viewId)
		*v = View{
			viewId:        viewId,
			gmapId:        gmapId,
			playSessionId: playSessionId,
		}

		eng.outEvents <- OutEvent{
			T:             OE_VIEW_CREATED,
			RoomId:        m.roomId,
			PlaySessionId: playSessionId,
			ViewId:        viewId,
		}
	}
}
