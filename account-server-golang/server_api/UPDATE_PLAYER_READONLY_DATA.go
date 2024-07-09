package server_api

import (
	"account-server/database"
	"account-server/gameservers"
	"account-server/utils"
	"encoding/json"
	"errors"

	"go.mongodb.org/mongo-driver/bson"
)

type request_UPDATE_PLAYER_READONLY_DATA struct {
	Request_id           string
	Lobby_id             string
	Ticket               string
	Player_readonly_data string
}

func UPDATE_PLAYER_READONLY_DATA(message []byte, sendResponse func([]byte)) error {

	var r request_UPDATE_PLAYER_READONLY_DATA

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "lobby_id", "ticket", "player_readonly_data"}) {
			err = errors.New("UPDATE_PLAYER_READONLY_DATA bad input parameters")
			return err
		}
	}

	err := json.Unmarshal(message, &r)
	if err != nil {
		return err
	}

	valid := false
	errorResponse := map[string]any{}

	lobbyId := r.Lobby_id

	playerSessionId, errorStr := gameservers.GetPlayerSessionId(lobbyId, r.Ticket)

	if playerSessionId != nil {
		if errorStr != "" {
			panic(0)
		}

		// gsie.RLock()
		// player, player_ok := gsie.Players[r.Ticket]
		// gsie.RUnlock()

		// if player_ok {

		var account bson.M

		data_dict := dict{} // El dict que se utilizara para hacer el merge con lo que llega en r.Player_readonly_data

		// Comprueba que existe una cuenta con el sessionId dado
		{
			target := []string{"session_id", *playerSessionId}

			projection := "session_id player_readonly_data"
			account, err = database.ReadAccount(target, projection)
			if err != nil {
				return err
			}
		}

		if account != nil {

			// Aqui se rellena data_dict con lo que hay en account["player_readonly_data"].
			{
				// ATENCION: Lo que hay en account["player_readonly_data"] es un str no un dict asi que hace falta convertirlo a dict.
				var undata dict
				err := json.Unmarshal([]byte(account["player_readonly_data"].(string)), &undata)
				if err != nil {
					return err
				}
				if _, ok := undata["maps_data"]; !ok {
					// ATENCION: Las keys que son dict deben ya existir en 'player_readonly_data' antes de poder hacer un merge_leafs
					undata["maps_data"] = dict{}
				}
				data_dict["player_readonly_data"] = undata
			}

			// Realiza el MergeDicts
			{
				var undata dict
				err := json.Unmarshal([]byte(r.Player_readonly_data), &undata)
				if err != nil {
					return err
				}
				utils.MergeDicts(data_dict, dict{"player_readonly_data": undata})
			}

			// Update player_readonly_data
			{
				target := []string{"session_id", *playerSessionId}
				update := bson.D{bson.E{}}
				{
					bytes, err := json.Marshal(data_dict["player_readonly_data"])
					if err != nil {
						return err
					}
					update[0] = bson.E{Key: "player_readonly_data", Value: string(bytes)}
				}
				// projection := "session_id player_readonly_data"

				err := database.UpdateAccount(target, update)
				if err != nil {
					panic(0)
				}

				for i := range update {
					pu := &update[i]
					account[pu.Key] = pu.Value
				}

				responseDict := account
				responseDict["request_id"] = r.Request_id
				responseDict["lobby_id"] = lobbyId
				responseDict["session_id"] = *playerSessionId

				var response []byte
				response, err = json.Marshal(responseDict)
				if err != nil {
					return err
				}
				sendResponse(response)
				valid = true
			}
		} else {
			errorResponse["error"] = "No account found with this session_id."
		}
		// } else {
		// 	errorResponse["error"] = "Invalid ticket. Ticket not found in game server list."
		// }
	} else {
		errorResponse["error"] = errorStr
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
