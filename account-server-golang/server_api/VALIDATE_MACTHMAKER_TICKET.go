package server_api

import (
	"account-server/database"
	"account-server/gameservers"
	"account-server/utils"
	"encoding/json"
	"errors"

	"go.mongodb.org/mongo-driver/bson"
)

type request_VALIDATE_MACTHMAKER_TICKET struct {
	Request_id         string
	Lobby_id           string
	Ticket             string
	Preferred_room_tag string
}

// VALIDATE_MACTHMAKER_TICKET:
// 1. Validates a Game Server session ticket and returns details about the user
func VALIDATE_MACTHMAKER_TICKET(message []byte, sendResponse func([]byte)) error {

	var r request_VALIDATE_MACTHMAKER_TICKET

	opt_preferred_room_tag := "" // Parametro opcional (con valor por defecto "") para request_VALIDATE_MACTHMAKER_TICKET

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "lobby_id", "ticket"}) {
			err = errors.New("VALIDATE_MACTHMAKER_TICKET bad input parameters")
			return err
		}

		if v, ok := m["preferred_room_tag"]; ok {
			opt_preferred_room_tag = v.(string)
		}
	}

	err := json.Unmarshal(message, &r)
	if err != nil {
		return err
	}
	r.Preferred_room_tag = opt_preferred_room_tag

	valid := false
	errorResponse := map[string]any{}

	// gsie := gameservers.GetGameServer(r.Lobby_id)

	// var vpticket gameservers.ValidationPendingTicket
	// var vpticket_ok bool
	// if gsie != nil {
	// 	gsie.RLock()
	// 	vpticket, vpticket_ok = gsie.ValidationPendingTickets[r.Ticket]
	// 	gsie.RUnlock()
	// 	if vpticket_ok {
	// 		gsie.Lock()
	// 		delete(gsie.ValidationPendingTickets, r.Ticket)
	// 		gsie.Unlock()
	// 	}
	// }

	validated_ticket, errorMsg := gameservers.ValidateTicket(r.Lobby_id, r.Ticket)

	if validated_ticket != nil {
		var account bson.M

		// Comprueba que existe una cuenta con el sessionId dado
		{
			target := []string{"session_id", validated_ticket.SessionId}

			projection := "account_name guest_account_id display_name player_data player_readonly_data"
			account, err = database.ReadAccount(target, projection)
			if err != nil {
				return err
			}
		}

		if account != nil { // Si existe la cuenta

			if roomId, errorStr := gameservers.AssignRoom(r.Lobby_id, validated_ticket, r.Preferred_room_tag); errorStr == "" {

				// selected_room_id := int(-1) // Inicializa aun valor no valido

				// gsie.Lock()
				// max_players_in_gameserver := gsie.Max_rooms * gsie.Max_players_per_room
				// notGameServerFull := uint(len(gsie.Players)) < max_players_in_gameserver
				// if notGameServerFull {

				// 	// Elige la primera Room que no este llena
				// 	// {
				// 	// 	for room_id := uint(0); room_id < gsie.Max_rooms; room_id++ {
				// 	// 		if gsie.RoomPlayerCount[room_id] < gsie.Max_players_per_room {
				// 	// 			selected_room_id = int(room_id)
				// 	// 			break
				// 	// 		}
				// 	// 	}

				// 	// 	if selected_room_id < 0 || selected_room_id >= int(gsie.Max_rooms) {
				// 	// 		panic("ERROR")
				// 	// 	}
				// 	// }

				// 	// FIXME: Elige la room aleatoriamente
				// 	selected_room_id = rand.Intn(int(gsie.Max_rooms))

				// 	gsie.Players[r.Ticket] = gameservers.Player{SessionId: vpticket.SessionId, RoomId: uint(selected_room_id)}

				// 	gsie.RoomPlayerCount[selected_room_id] += 1
				// }
				// gsie.Unlock()

				responseDict := account
				responseDict["request_id"] = r.Request_id
				responseDict["lobby_id"] = r.Lobby_id
				responseDict["session_id"] = validated_ticket.SessionId
				responseDict["room_id"] = roomId

				var response []byte
				response, err = json.Marshal(responseDict)
				if err != nil {
					return err
				}
				sendResponse(response)
				valid = true

			} else {
				errorResponse["error"] = errorStr
			}
		} else {
			errorResponse["error"] = "No account found."
		}
	} else {
		errorResponse["error"] = errorMsg
	}

	if !valid {
		var errorResponseBytes []byte
		errorResponseBytes, err = json.Marshal(errorResponse)
		if err != nil {
			return err
		}
		sendResponse(errorResponseBytes)
	}

	return err
}
