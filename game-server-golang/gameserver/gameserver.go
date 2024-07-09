package main

import (
	"fmt"
	"sync"

	"github.com/gofiber/websocket/v2"

	"common/pool"
	"gameserver-go/engine"
	"gameserver-go/slots"
)

const (
	MAX_NUMBER_OF_PLAYERS_PER_ROOM     = 32
	MAX_NUMBER_OF_USERS_PER_ROOM       = MAX_NUMBER_OF_PLAYERS_PER_ROOM + 4
	MAX_NUMBER_OF_ROOMS                = 1
	MAX_NUMBER_OF_SLOTS                = MAX_NUMBER_OF_USERS_PER_ROOM * MAX_NUMBER_OF_ROOMS
	MAX_NUMBER_OF_USERS                = MAX_NUMBER_OF_SLOTS
	MAX_INPUT_STATES_PER_USER_AND_STEP = 5
)

const (
	MSG_COMPRESSED = 0x01
	MSG_INTERNAL   = 0x02
)

const (
	MSG_INTERNAL_NONE = iota
	MSG_INTERNAL_PING
	MSG_INTERNAL_PONG
	MSG_INTERNAL_BIND_REQUEST // Indica que el cliente tiene la intencion de hacer bind en el slot.
)

var gameServer *GameServer

type GameServer struct {
	valid        bool // El zero value de GameServer es cuando valid es false.
	config       Config
	slots        pool.ObjectPool[slots.Slot]
	users        pool.ObjectPool[User]
	rooms        pool.ObjectPool[Room]
	events       chan Event           // chan mediante el cual el loop fiber se puede comunicar con el loop gameserver enviandole eventos.
	engineEvents chan engine.OutEvent // chan para recibir eventos que envia el engine.
}

const (
	GS_EVENT_ADD_ROOM_REQUESTED = iota
)

type Event struct {
	eventType int
}

type User struct {
	userId         int  // Id de este user. Es el id que tiene el user en GameServer.users
	slotId         int  // Id del slot al que esta asociado este user. Es el id que tiene el slot en GameServer.slots
	hasPlaySession bool // Indica si el user tiene una play session asociada.
	playSessionId  int  // Si hasPlaySession es true entonces playSessionId indica el id de la play session.
}

type PlaySession struct {
	valid         bool
	playSessionId int // Id de esta play session. Es el id que tiene la play session en GameServer.rooms[roomId].playSessions
	roomId        int // Id de la room a la que esta asociada esta play session. Es el id que tiene la room en GameServer.rooms
	userId        int // Id del user al que esta asociada esta play session. Es el id que tiene el user en GameServer.users
	hasView       bool
	viewId        int
}

type Room struct {
	valid        bool // El zero value de Room es cuando valid es false.
	roomId       int
	gmapId       int
	playSessions pool.ObjectPool[PlaySession]

	inputStateBufferLock sync.Mutex
	inputStateBuffer     [MAX_NUMBER_OF_PLAYERS_PER_ROOM * MAX_INPUT_STATES_PER_USER_AND_STEP][]byte
}

func (p *PlaySession) Make(viewId int, playSessionId int, roomId int, userId int) {
	*p = PlaySession{
		valid:         true,
		viewId:        viewId,
		playSessionId: playSessionId,
		roomId:        roomId,
		userId:        userId,
	}
}

func (p *PlaySession) Destroy() {
	*p = PlaySession{}
}

func (r *Room) Make(roomId int, gmapId int) {
	*r = Room{
		valid:  true,
		roomId: roomId,
		gmapId: gmapId,
	}
	r.playSessions.Make(MAX_NUMBER_OF_PLAYERS_PER_ROOM)
}

func (r *Room) Destroy() {
	*r = Room{}
}

func (r *Room) AddUser(userId int) int {
	if !r.valid {
		panic(0)
	}

	playSessionId := int(-1)

	if playSessionId = r.playSessions.Alloc(); playSessionId >= 0 {
		ps := r.playSessions.GetObject(playSessionId)
		ps.valid = false
		// *ps = PlaySession{
		// 	valid:         true,
		// 	playSessionId: playSessionId,
		// 	roomId:        r.roomId,
		// 	userId:        userId,
		// 	hasView:       false,
		// }

		// fmt.Println("User[", userId, "] ADDED to Room[", r.roomId, "] PlaySession[", playSessionId, "] with no View.")
	}
	return playSessionId
}

func (gs *GameServer) Make(config *Config) {
	gs.valid = true
	gs.config = *config

	gs.slots.Make(MAX_NUMBER_OF_SLOTS)
	gs.users.Make(MAX_NUMBER_OF_USERS)
	gs.rooms.Make(MAX_NUMBER_OF_ROOMS)

	gs.events = make(chan Event, 64)
	gs.engineEvents = make(chan engine.OutEvent, 1024)

	// Crea una room
	// if roomId := gameServer.rooms.Alloc(); roomId >= 0 {
	// 	r := gs.rooms.GetObject(roomId)
	// 	r.playSessions.Initialize(MAX_NUMBER_OF_PLAYERS_PER_ROOM)
	// }
}

func (gs *GameServer) AddRoomRequest() {
	gs.events <- Event{GS_EVENT_ADD_ROOM_REQUESTED}
}

// func (gs *GameServer) addRoom(gmapId int) {
// 	if roomId := gameServer.rooms.Alloc(); roomId >= 0 {
// 		r := gameServer.rooms.GetObject(roomId)
// 		*r = Room{
// 			gmapId: gmapId,
// 		}

// 		r.playSessions.Initialize(MAX_NUMBER_OF_PLAYERS_PER_ROOM)

// 		fmt.Println("ADDED Room: ", roomId, " with Gmap: ", gmapId)
// 	}
// }

func gameServerLoop(registry chan WebsocketClient, messageQueue chan WebsocketMessage) {
	for {
		select {
		case ev := <-gameServer.events:
			if ev.eventType == GS_EVENT_ADD_ROOM_REQUESTED {
				if !gameServer.rooms.Full() {
					if roomId := gameServer.rooms.Alloc(); roomId >= 0 {
						// r := gameServer.rooms.GetObject(roomId)
						// *r = Room{}
						fmt.Println("ADDED Room:", roomId, "with no Gmap.")
						engine.CreateGMap(roomId)
					}
				}
			}
		case engEv := <-gameServer.engineEvents:
			if engEv.T == engine.OE_GMAP_CREATED {
				r := gameServer.rooms.GetObject(engEv.RoomId)
				r.Make(engEv.RoomId, engEv.GMapId)

				fmt.Println("CREATED GMap:", engEv.GMapId, "for Room:", engEv.RoomId)
			} else if engEv.T == engine.OE_VIEW_CREATED {
				r := gameServer.rooms.GetObject(engEv.RoomId)
				r.Make(engEv.RoomId, engEv.GMapId)

				fmt.Println("CREATED View:", engEv.ViewId, "for Room:", engEv.RoomId, "PlaySessionId[", engEv.PlaySessionId, "]")
			}
		case wsc := <-registry:
			if wsc.OperationType == slots.RegistryOperationAcquireSlot {
				if slotId := gameServer.slots.Alloc(); slotId >= 0 {
					s := gameServer.slots.GetObject(slotId)
					*s = slots.Slot{
						C:                wsc.C,
						SlotId:           slotId,
						IsAssignedToUser: false,
					}

					wsc.Control <- websocketControl{slotId}
					fmt.Println("ADDED Slot: ", slotId)

				}
			} else if wsc.OperationType == slots.RegistryOperationReleaseSlot {
				if wsc.SlotId >= 0 {
					s := gameServer.slots.GetObject(wsc.SlotId)
					if s.C != nil && s.UserId >= 0 {
						if gameServer.users.IsValidObject(s.UserId) {
							u := gameServer.users.GetObject(s.UserId)
							*u = User{}
							gameServer.users.Free(s.UserId)
							fmt.Println("REMOVED User: ", s.UserId)
						} else {
							panic(0)
						}
					}

					*s = slots.Slot{}
					gameServer.slots.Free(wsc.SlotId)
					fmt.Println("REMOVED Slot: ", wsc.SlotId)
				}
			}
		case msg := <-messageQueue:
			fmt.Printf("Slot[%d] Message received: %v\n", msg.slotId, msg)
			if msg.slotId >= 0 {
				//
				// Para cada mensaje recibido por el websocket el primer byte del mensaje contiene flags.
				// 	MSG_COMPRESSED = 0x01,  // Indica que el mensaje esta comprimido. Solo se aplica si el opCode es uWS::BINARY.
				// 	MSG_INTERNAL   = 0x02   // Indica que el mensaje es un mensaje interno. IMPORTANTE: Los mensajes internos nunca se comprimen.
				//
				// El segundo byte contiene un id de token.
				// Para los mensajes que son MSG_INTERNAL los tokens son:
				// 	NONE = 0        ,
				// 	PING            ,
				// 	PONG            ,
				// 	BIND_REQUEST // Indica que el cliente tiene la intencion de hacer bind en el slot.
				//

				if (msg.data[0]&MSG_INTERNAL) != 0 && msg.data[1] == MSG_INTERNAL_BIND_REQUEST {
					fmt.Println("BIND_REQUEST received")
					// Crea un nuevo User
					if userId := gameServer.users.Alloc(); userId >= 0 {
						// Inicializa el user asignandole el userId y el slotId.
						u := gameServer.users.GetObject(userId)
						*u = User{
							userId:         userId,
							slotId:         msg.slotId,
							hasPlaySession: false,
						}

						// Asigna el user al slot de manera que, cuando el slot sea liberado, este sepa que user debe liberar.
						s := gameServer.slots.GetObject(msg.slotId)
						s.IsAssignedToUser = true
						s.UserId = userId

						fmt.Println("ADDED User: ", userId)

						// Elije una Room para asignarsela al user
						roomId := 0
						room := gameServer.rooms.GetObject(roomId)

						// Inserta al user en la room
						playSessionId := room.AddUser(userId)
						if playSessionId >= 0 {
							engine.CreateView(room.gmapId, playSessionId)
						}						
					}
				}

				if err := gameServer.slots.GetObject(msg.slotId).C.WriteMessage(websocket.BinaryMessage, msg.data); err != nil {
					panic(err)
				}
			}
		}
	}
}
