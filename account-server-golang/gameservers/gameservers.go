package gameservers

import (
	"account-server/utils"
	"fmt"
	"time"
)

// Tiempo maximo que puede pasar hasta recibir un REFRESH_GAMESERVER_INSTANCE_STATE.
// Si se pasa entonces el gameserver instance sera eliminado del map.
const gameServerRefreshTimeout = time.Minute * 1 // Un minuto.
const removeExpiredvalidationPendingTicketsInterval = time.Second * 5
const removeLostGameServersInterval = time.Second * 6

// Tiempo maximo que un ticket puede estar sin validar (ver VALIDATE_MACTHMAKER_TICKET).
// Si se pasa entonces el ticket sera eliminado de la lista de tickets.
const gameServervalidationPendingTicketTimeout = time.Second * 15

var g_gameServersInfo = gameServersInfo{
	Instances: map[string]*gameServerInfoEntry{},
	RoomTags:  map[string]*RoomTagEntry{},
}

func removeExpiredvalidationPendingTickets() {
	// Elimina los tickets caducados.
	gservers := g_gameServersInfo.Instances
	for _, gsie := range gservers {
		// Cuidado: Se eliminan elementos de <gsie.validationPendingTickets> mientras se recorre. Es necesario hacerlo en dos pasos.
		removed_tickets := make([]string, 0, 128)

		for t, v := range gsie.validationPendingTickets {
			expireTime, err := time.Parse(time.RFC3339, v.ExpireTime)
			if err != nil {
				panic(0)
			}
			if time.Now().After(expireTime) {
				removed_tickets = append(removed_tickets, t)
			}
		}

		for _, t := range removed_tickets {
			delete(gsie.validationPendingTickets, t)
		}
	}
}

func removeLostGameServers() {
	// Elimina los gameservers que no han recibido REFRESH_GAMESERVER_INSTANCE_STATE.
	// Cuidado: Se eliminan elementos de <g_gameServersInfo.Instances> mientras se recorre. Es necesario hacerlo en dos pasos.
	removed_gameservers := make([]*gameServerInfoEntry, 0, 128)

	gservers := g_gameServersInfo.Instances
	for _, gsie := range gservers {
		expireTime, err := time.Parse(time.RFC3339, gsie.Expire_time)
		if err != nil {
			panic(0)
		}
		if time.Now().After(expireTime) {
			removed_gameservers = append(removed_gameservers, gsie)
		}
	}

	for _, gsie := range removed_gameservers {
		delete(g_gameServersInfo.Instances, gsie.Lobby_id)
	}
}

func init() {
	go process()
}

type operation struct {
	OperationId uint
	Params      []any
	response    chan callOperationResponse
}

type callOperationResponse struct {
	Response any
	ErrorStr string // Si la string no esta vacia indica que ha habido error y Response no es valido.
}

var operations chan *operation = make(chan *operation, 100)

const (
	_OP_GET_GAMESERVERS = iota
	_OP_EXISTS_GAMESERVER
	_OP_ADD_GAMESERVER
	_OP_ASSIGN_ROOM
	_OP_GET_PLAYER_SESSION_ID
	_OP_REFRESH_GAMESERVER
	_OP_REMOVE_GAMESERVER
	_OP_REMOVE_GAMESERVER_BY_ADDRESS_AND_PORT
	_OP_VALIDATE_TICKET
	_OP_NOTIFY_MATCHMAKER_PLAYER_LEFT
	_OP_MATCHMAKE
)

var operationsTable = map[uint]func(op *operation){
	_OP_GET_GAMESERVERS:                       exec_OP_GET_GAMESERVERS,
	_OP_EXISTS_GAMESERVER:                     exec_OP_EXISTS_GAMESERVER,
	_OP_ADD_GAMESERVER:                        exec_OP_ADD_GAMESERVER,
	_OP_ASSIGN_ROOM:                           exec_OP_ASSIGN_ROOM,
	_OP_GET_PLAYER_SESSION_ID:                 exec_OP_GET_PLAYER_SESSION_ID,
	_OP_REFRESH_GAMESERVER:                    exec_OP_REFRESH_GAMESERVER,
	_OP_REMOVE_GAMESERVER:                     exec_OP_REMOVE_GAMESERVER,
	_OP_REMOVE_GAMESERVER_BY_ADDRESS_AND_PORT: exec_OP_REMOVE_GAMESERVER_BY_ADDRESS_AND_PORT,
	_OP_VALIDATE_TICKET:                       exec_OP_VALIDATE_TICKET,
	_OP_NOTIFY_MATCHMAKER_PLAYER_LEFT:         exec_OP_NOTIFY_MATCHMAKER_PLAYER_LEFT,
	_OP_MATCHMAKE:                             exec_OP_MATCHMAKE,
}

func callOperation(op_id uint, params ...any) callOperationResponse {
	// fmt.Printf("callOperation[%d] started\n", op_id)
	op := operation{
		OperationId: op_id,
		Params:      params,
	}
	op.response = make(chan callOperationResponse)

	operations <- &op

	// fmt.Printf("callOperation[%d] waiting response\n", op_id)
	// response := <-op.response
	// fmt.Printf("callOperation[%d] received response\n", op_id)
	return <-op.response
}

func execOperation(op *operation) {
	operationsTable[op.OperationId](op)
}

func process() {
	removeExpiredvalidationPendingTicketsTicker := time.NewTicker(removeExpiredvalidationPendingTicketsInterval)
	removeLostGameServersTicker := time.NewTicker(removeLostGameServersInterval)
	for {
		select {
		case op := <-operations:
			execOperation(op)
		case <-removeExpiredvalidationPendingTicketsTicker.C:
			removeExpiredvalidationPendingTickets()
		case <-removeLostGameServersTicker.C:
			removeLostGameServers()
		}
	}
}

func buildGameServersSnapshotsList() []*GameServerSnapshot {
	result := make([]*GameServerSnapshot, 0, 64)

	for _, gsie := range g_gameServersInfo.Instances {
		d := GameServerSnapshot{
			GameServerSpec: gsie.GameServerSpec,
			PlayerCount:    uint(len(gsie.Players)),
			GameName:       gsie.Game["game_name"],
			MapName:        gsie.Game["map_name"],
		}
		result = append(result, &d)
	}

	return result
}

func ExistGameServer(lobbyId string) bool {
	cr := callOperation(_OP_EXISTS_GAMESERVER, lobbyId)
	return cr.Response.(bool)
}

func ValidateTicket(lobbyId string, ticket string) (*ValidatedTicket, string) {
	cr := callOperation(_OP_VALIDATE_TICKET, lobbyId, ticket)
	if cr.Response == nil {
		return nil, cr.ErrorStr
	} else {
		return cr.Response.(*ValidatedTicket), cr.ErrorStr
	}
}

func NotifyMatchmakerPlayerLeft(lobbyId string, vticket string) (*string, string) {
	cr := callOperation(_OP_NOTIFY_MATCHMAKER_PLAYER_LEFT, lobbyId, vticket)
	return cr.Response.(*string), cr.ErrorStr
}

func AssignRoom(lobbyId string, vticket *ValidatedTicket, preferred_room_tag string) (uint, string) {
	cr := callOperation(_OP_ASSIGN_ROOM, lobbyId, vticket, preferred_room_tag)
	return cr.Response.(uint), cr.ErrorStr
}

func GetGameServer(lobbyId string) *GameServerSnapshot {
	var result *GameServerSnapshot

	if gsie, ok := g_gameServersInfo.Instances[lobbyId]; ok {
		d := GameServerSnapshot{
			GameServerSpec: gsie.GameServerSpec,
			PlayerCount:    uint(len(gsie.Players)),
			GameName:       gsie.Game["game_name"],
			MapName:        gsie.Game["map_name"],
		}
		result = &d
	}

	return result
}

func GetGameServers() []*GameServerSnapshot {
	cr := callOperation(_OP_GET_GAMESERVERS)
	return cr.Response.([]*GameServerSnapshot)
}

func GetPlayerSessionId(lobbyId string, vticket string) (*string, string) {
	cr := callOperation(_OP_GET_PLAYER_SESSION_ID, lobbyId, vticket)
	if cr.Response == nil {
		return nil, cr.ErrorStr
	} else {
		return cr.Response.(*string), cr.ErrorStr
	}
}

func AddGameServer(gss *GameServerSpec, game map[string]string) {
	callOperation(_OP_ADD_GAMESERVER, gss, game)
}

// RefreshGameServer actualiza el refresh expire time del gameserver.
func RefreshGameServer(lobbyId string, currentMap string) bool {
	cr := callOperation(_OP_REFRESH_GAMESERVER, lobbyId, currentMap)
	return cr.Response.(bool)
}

func RemoveGameServer(lobbyId string) {
	callOperation(_OP_REMOVE_GAMESERVER, lobbyId)
}

func RemoveGameServersByAddressAndPort(ipv4_address string, port uint) {
	callOperation(_OP_REMOVE_GAMESERVER_BY_ADDRESS_AND_PORT, ipv4_address, port)
}

// Devuelve (ticket, lobbyId)
func MatchMake(gameName string, preferred_region string, preferred_lobby_id string, preferred_room_tag string, sessionId string) (string, string) {
	cr := callOperation(_OP_MATCHMAKE, gameName, preferred_region, preferred_lobby_id, preferred_room_tag, sessionId)
	s := cr.Response.([]string)
	return s[0], s[1]
}

func exec_OP_GET_GAMESERVERS(op *operation) {
	gservers := buildGameServersSnapshotsList()
	op.response <- callOperationResponse{gservers, ""}
}

func exec_OP_EXISTS_GAMESERVER(op *operation) {
	lobbyId := op.Params[0].(string)
	var errorStr string
	if _, ok := g_gameServersInfo.Instances[lobbyId]; ok {
		op.response <- callOperationResponse{true, errorStr}
	} else {
		op.response <- callOperationResponse{false, errorStr}
	}
}

func exec_OP_ADD_GAMESERVER(op *operation) {
	gss := op.Params[0].(*GameServerSpec)
	game := op.Params[1].(map[string]string)
	gsi := &gameServerInfo{
		GameServerSpec:  gss,
		Game:            game,
		RoomPlayerCount: make([]uint, gss.Max_rooms),
	}

	gsie := &gameServerInfoEntry{gameServerInfo: *gsi}
	gsie.Expire_time = time.Now().Add(gameServerRefreshTimeout).Format(time.RFC3339)
	gsie.validationPendingTickets = map[string]validationPendingTicket{}
	gsie.Players = map[string]player{}

	g_gameServersInfo.Instances[gsi.Lobby_id] = gsie

	op.response <- callOperationResponse{}
}

func exec_OP_ASSIGN_ROOM(op *operation) {
	lobbyId := op.Params[0].(string)
	vticket := op.Params[1].(*ValidatedTicket)
	preferredRoomTag := op.Params[2].(string)

	selected_room_id := int(-1) // Inicializa aun valor no valido

	var errorStr string

	var roomTag *RoomTagEntry
	if preferredRoomTag != "" {
		if v, ok := g_gameServersInfo.RoomTags[preferredRoomTag]; ok {
			lobbyId = v.LobbyId
			roomTag = v
		} else {
			fmt.Println("Warning: preferredRoomTag[" + preferredRoomTag + "] not found in g_gameServersInfo.RoomTags.")
			preferredRoomTag = "" // Desactiva la seleccion de room mediante preferredRoomTag.
		}
	}

	if gsie, ok := g_gameServersInfo.Instances[lobbyId]; ok {

		max_players_in_gameserver := gsie.Max_rooms * gsie.Max_players_per_room
		notGameServerFull := uint(len(gsie.Players)) < max_players_in_gameserver
		if notGameServerFull {

			// Elige la primera Room que no este llena
			{
				for room_id := uint(0); room_id < gsie.Max_rooms; room_id++ {
					if gsie.RoomPlayerCount[room_id] < gsie.Max_players_per_room {
						selected_room_id = int(room_id)
						break
					}
				}

				if selected_room_id < 0 || selected_room_id >= int(gsie.Max_rooms) {
					panic("ERROR")
				}
			}

			if preferredRoomTag != "" {
				if roomTag == nil {
					panic(0)
				}

				if !roomTag.RoomIdValid {
					rid := int(-1)
					// Elige la Room, que no este llena, que tenga mas slots libres.
					{
						min_room_player_count := uint(1000000)
						for room_id := uint(0); room_id < gsie.Max_rooms; room_id++ {
							player_count := gsie.RoomPlayerCount[room_id]
							if player_count < gsie.Max_players_per_room && player_count < min_room_player_count {
								min_room_player_count = player_count
								rid = int(room_id)
							}
						}

						if rid < 0 || rid >= int(gsie.Max_rooms) {
							panic("ERROR")
						}
					}
					if rid >= 0 {
						roomTag.RoomIdValid = true
						roomTag.RoomId = uint(rid)
						selected_room_id = int(roomTag.RoomId)
					} else {
						errorStr = "Preferred room is full."
					}
				} else {
					selected_room_id = int(roomTag.RoomId)
				}
			} else {
				// FIXME: Elige la room aleatoriamente
				// selected_room_id = rand.Intn(int(gsie.Max_rooms))
			}

			if selected_room_id > 0 {
				gsie.Players[vticket.ticket] = player{SessionId: vticket.SessionId, RoomId: uint(selected_room_id)}
				gsie.RoomPlayerCount[selected_room_id] += 1
			}
		}

		if !notGameServerFull {
			errorStr = "Game server is full."
		}
	} else {
		if preferredRoomTag != "" {
			errorStr = "Game server, linked to RoomTag, not found."
		} else {
			errorStr = "Game server not found."
		}
	}

	var room_id uint
	if errorStr == "" {
		if selected_room_id < 0 {
			panic(0)
		}
		room_id = uint(selected_room_id)
	}

	op.response <- callOperationResponse{room_id, errorStr}
}

func exec_OP_GET_PLAYER_SESSION_ID(op *operation) {
	lobbyId := op.Params[0].(string)
	vticket := op.Params[1].(string)

	var errorStr string

	if gsie, ok := g_gameServersInfo.Instances[lobbyId]; ok {
		if player, player_ok := gsie.Players[vticket]; player_ok {
			op.response <- callOperationResponse{&player.SessionId, errorStr}
			return
		} else {
			errorStr = "Invalid ticket. Ticket not found in game server list."
		}
	} else {
		errorStr = "Game server not found."
	}
	op.response <- callOperationResponse{nil, errorStr}
}

func exec_OP_REFRESH_GAMESERVER(op *operation) {
	lobbyId := op.Params[0].(string)
	currentMap := op.Params[1].(string)
	if gsie, ok := g_gameServersInfo.Instances[lobbyId]; ok {
		expireTime, err := time.Parse(time.RFC3339, gsie.Expire_time)
		if err != nil {
			panic(0)
		}
		gsie.Game["map_name"] = currentMap

		if expireTime.After(time.Now()) {
			gsie.Expire_time = time.Now().Add(gameServerRefreshTimeout).Format(time.RFC3339)
		}
		op.response <- callOperationResponse{true, ""}
	} else {
		op.response <- callOperationResponse{false, ""}
	}
}

func exec_OP_REMOVE_GAMESERVER(op *operation) {
	lobbyId := op.Params[0].(string)
	removeRoomTagsLinkedToLobbyId(lobbyId)
	delete(g_gameServersInfo.Instances, lobbyId)
	op.response <- callOperationResponse{}
}

func exec_OP_REMOVE_GAMESERVER_BY_ADDRESS_AND_PORT(op *operation) {
	ipv4_address := op.Params[0].(string)
	port := op.Params[1].(uint)

	gservers := buildGameServersSnapshotsList()
	for _, gsie := range gservers {
		if gsie.Ipv4_address == ipv4_address && gsie.Port == port {
			removeRoomTagsLinkedToLobbyId(gsie.Lobby_id)
			delete(g_gameServersInfo.Instances, gsie.Lobby_id)
		}
	}
	op.response <- callOperationResponse{}
}

func exec_OP_VALIDATE_TICKET(op *operation) {
	lobbyId := op.Params[0].(string)
	ticket := op.Params[1].(string)

	var errorStr string

	if gsie, ok := g_gameServersInfo.Instances[lobbyId]; ok {
		vpticket, vpticket_ok := gsie.validationPendingTickets[ticket]
		if vpticket_ok {
			delete(gsie.validationPendingTickets, ticket)
			op.response <- callOperationResponse{&ValidatedTicket{ticket, vpticket.SessionId}, errorStr}
			return
		} else {
			errorStr = "Ticket not found."
		}
	} else {
		errorStr = "Game server not found."
	}
	op.response <- callOperationResponse{nil, errorStr}
}

func exec_OP_NOTIFY_MATCHMAKER_PLAYER_LEFT(op *operation) {
	lobbyId := op.Params[0].(string)
	vticket := op.Params[1].(string)

	var errorStr string
	var sessionId *string

	if gsie, ok := g_gameServersInfo.Instances[lobbyId]; ok {
		if player, ok := gsie.Players[vticket]; ok {
			sessionId = &player.SessionId
			delete(gsie.Players, vticket)

			if gsie.RoomPlayerCount[player.RoomId] == 0 {
				panic("ERROR")
			}
			gsie.RoomPlayerCount[player.RoomId] -= 1
		} else {
			errorStr = "Invalid ticket. Ticket not found in game server list."
		}
	} else {
		errorStr = "Game server not found."
	}
	op.response <- callOperationResponse{sessionId, errorStr}
}

func exec_OP_MATCHMAKE(op *operation) {
	gameName := op.Params[0].(string)
	preferred_region := op.Params[1].(string)
	preferred_lobby_id := op.Params[2].(string)
	preferred_room_tag := op.Params[3].(string)
	sessionId := op.Params[4].(string)

	var ret_ticket string
	var ret_gsie *gameServerInfoEntry

	errorStr := ""

	// Comprueba que no exista ya un ticket para ese session_id
	{
		exit_loop := false
		for _, gsie := range g_gameServersInfo.Instances {
			if exit_loop {
				break
			}

			for tk, tk_data := range gsie.validationPendingTickets {
				if tk_data.SessionId == sessionId {
					ret_ticket = tk
					ret_gsie = gsie
					exit_loop = true
					break
				}
			}

			for tk, player := range gsie.Players {
				if player.SessionId == sessionId {
					ret_ticket = tk
					ret_gsie = gsie
					exit_loop = true
					break
				}
			}
		}
	}

	// Si no existe ya un ticket entonces crea uno nuevo.
	if ret_ticket == "" {
		gss := make([]struct {
			LobbyId string
			GSIE    *gameServerInfoEntry
		}, 0, 64)

		if preferred_room_tag != "" {
			if v, ok := g_gameServersInfo.RoomTags[preferred_room_tag]; ok {
				v.LastAccessTime = time.Now()
				preferred_lobby_id = v.LobbyId // Sobreescribe preferred_lobby_id con el lobbyId asociado al preferred_room_tag.
				preferred_region = ""          // Desactiva la seleccion por region para permitir la seleccion por lobby_id.
			}
		}

		// Recopila en <gss> los gameservers que cumplen todas las siguientes condiciones:
		//	- tienen algun slot libre
		//	- estan sirviendo el juego <gameName>.
		//	- esta en la region <preferred_region> si <preferred_region> es != "".
		//	- cuyo lobby_id es <preferred_lobby_id> si <preferred_lobby_id> != "".
		for _, gsie := range g_gameServersInfo.Instances {
			if uint(len(gsie.Players)) < gsie.Max_players_per_room && gsie.Game["game_name"] == gameName {
				if preferred_region == "" || preferred_region == gsie.Region {
					if preferred_lobby_id == "" || preferred_lobby_id == gsie.Lobby_id {
						entry := struct {
							LobbyId string
							GSIE    *gameServerInfoEntry
						}{gsie.Lobby_id, gsie}
						gss = append(gss, entry)
					}
				}
			}
		}

		// Si no se ha encontrado ningun gameserver que cumpla las condiciones, entonces se
		// vuelve a buscar los gameservers que cumplen todas las siguientes condiciones:
		//	- tienen algun slot libre
		//	- estan sirviendo el juego <gameName>.
		if len(gss) == 0 {
			for _, gsie := range g_gameServersInfo.Instances {
				if uint(len(gsie.Players)) < gsie.Max_players_per_room && gsie.Game["game_name"] == gameName {
					entry := struct {
						LobbyId string
						GSIE    *gameServerInfoEntry
					}{gsie.Lobby_id, gsie}
					gss = append(gss, entry)
				}
			}
		}

		if len(gss) > 0 {
			// Elige el primer gameserver de la lista
			selected_index := 0
			gsie := gss[selected_index].GSIE
			ret_gsie = gsie

			// Crea ticket para <sessionId>
			{
				tickets := gsie.validationPendingTickets

				ret_ticket = utils.GenerateRandomString(32)

				tickets[ret_ticket] = validationPendingTicket{
					SessionId:  sessionId,
					ExpireTime: time.Now().Add(gameServervalidationPendingTicketTimeout).Format(time.RFC3339),
				}

				// fmt.Printf("Tickets asignados %d/%d\n", len(gsie.Players), gsie.Max_player_count)
				// fmt.Printf("Tickets pendientes de validacion %d\n", len(ret_ticket))
			}

			if preferred_room_tag != "" {
				if v, ok := g_gameServersInfo.RoomTags[preferred_room_tag]; !ok {
					// Asocia <ret_gsie.Lobby_id> al room tag <preferred_room_tag>.
					g_gameServersInfo.RoomTags[preferred_room_tag] = &RoomTagEntry{
						LobbyId:        ret_gsie.Lobby_id,
						LastAccessTime: time.Now(),
					}
					fmt.Printf("MATCHMAKE: Game server linked to RoomTag: %s", preferred_room_tag)
				} else {
					if v.LobbyId != ret_gsie.Lobby_id {
						// El LobbyId al que estaba asociada la RoomTagEntry ya no existe
						// asi que hay que eliminar la entrada de g_gameServersInfo.RoomTags
						// y notificar error.
						delete(g_gameServersInfo.RoomTags, preferred_room_tag)
						fmt.Printf("MATCHMAKE: Game server, linked to RoomTag: <%s>, not found.", preferred_room_tag)
						// errorStr = "Game server, linked to RoomTag, not found."
					}
				}
			}
		}
	}

	if ret_ticket != "" && ret_gsie == nil {
		panic(0)
	}

	var ret_lobby_id string
	if ret_gsie != nil {
		ret_lobby_id = ret_gsie.Lobby_id
	}

	op.response <- callOperationResponse{[]string{ret_ticket, ret_lobby_id}, errorStr}
}

// Elimina de g_gameServersInfo.RoomTags los roomTags que estan asociados a lobbyId.
// Ademas, elimina los roomTags que no hayan sido accedidos en un dia desde su ultimo acceso.
func removeRoomTagsLinkedToLobbyId(lobbyId string) {

	room_tags_to_delete := []string{}

	for roomTag, v := range g_gameServersInfo.RoomTags {
		if v.LobbyId == lobbyId {
			room_tags_to_delete = append(room_tags_to_delete, roomTag)
		} else {
			if time.Now().After(v.LastAccessTime.Add(time.Hour * 24)) {
				room_tags_to_delete = append(room_tags_to_delete, roomTag)
			}
		}
	}

	for i := range room_tags_to_delete {
		delete(g_gameServersInfo.RoomTags, room_tags_to_delete[i])
	}
}

type dict = map[string]any

type GameServerSnapshot struct {
	*GameServerSpec
	GameName    string
	MapName     string
	PlayerCount uint
}

type GameServerSpec struct { // Es la informacion inmutable que especifica a una instancia de game server.
	Lobby_id             string
	Build_id             string
	Ipv4_address         string
	Address              string // Se debe utilizar esta direccion para las conexiones SSL.
	Port                 uint
	Region               string
	Max_rooms            uint
	Max_players_per_room uint
	Server_name          string
}

type player struct {
	SessionId string // - session_id Identifica al player.
	RoomId    uint   // El id de la Room a la que fue asignado el Player en el MatchMake.
}

type ValidatedTicket struct { // Usado por ValidateTicket
	ticket    string
	SessionId string
}

type validationPendingTicket struct {
	SessionId  string // Identifica al cliente al que se ha asignado el ticket.
	ExpireTime string // Tiempo en el que el ticket dejara de ser valido y debera ser eliminado de tickets.
}

type gameServerInfo struct {
	*GameServerSpec // Esta informacion nunca debe ser modificada despues de su primera asignacion.

	Game        map[string]string // Es un dict con dos keys: {game_name: string, map_name: string}
	Expire_time string
	// validationPendingTickets es un dict indexado por ticket y sus valores son validationPendingTicket
	//   - ticket        El ticket se genera cuando el account server recibe el mensaje MATCHMAKE.
	//                   El player usara el ticket para conectarse al game server.
	// Contiene los tickets que estan pendientes de validacion.
	//   - session_id    Identifica al cliente al que se ha asignado el ticket.
	//   - session_expire   Tiempo en el que el ticket dejara de ser valido y debera ser eliminado de tickets.
	validationPendingTickets map[string]validationPendingTicket
	// players es un dict indexado por ticket y sus valores son session_id
	// Contiene los players que estan ocupando un slot en el gameserver.
	// - ticket  El ticket que se valida cuando el account server recibe el mensaje VALIDATE_MACTHMAKER_TICKET
	//           por parte del game server, y que este utilizara para identificar al player
	//           que ocupa uno de sus slots. Cuando se recibe VALIDATE_MACTHMAKER_TICKET, ticket se elimina de tickets
	//           y se inserta en players.
	Players         map[string]player
	RoomPlayerCount []uint // Numero de players que hay en cada Room. Cada player (es cliente con un ticket validado) esta ocupando un slot en el gameserver.
}

type gameServerInfoEntry struct {
	gameServerInfo
}

type gameServersInfo struct {
	Instances map[string]*gameServerInfoEntry // Mapa de gameserver instances. Estan indexadas por lobby_id.
	RoomTags  map[string]*RoomTagEntry        // Asocia una room tag con un lobby_id.
}

type RoomTagEntry struct {
	LobbyId        string
	LastAccessTime time.Time
	RoomIdValid    bool
	RoomId         uint
}
