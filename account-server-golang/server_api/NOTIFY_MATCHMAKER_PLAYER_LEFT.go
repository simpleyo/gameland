package server_api

import (
	"account-server/database"
	"account-server/gameservers"
	"account-server/utils"
	"encoding/json"
	"errors"

	"go.mongodb.org/mongo-driver/bson"
)

type request_NOTIFY_MATCHMAKER_PLAYER_LEFT struct {
	Request_id string
	Lobby_id   string
	Ticket     string
	Exit_data  dict
}

// NOTIFY_MATCHMAKER_PLAYER_LEFT:
// 1. Informs the match-making service that the user specified has left the Game Server Instance
func NOTIFY_MATCHMAKER_PLAYER_LEFT(message []byte, sendResponse func([]byte)) error {

	var r request_NOTIFY_MATCHMAKER_PLAYER_LEFT

	contains_exit_data := false

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "lobby_id", "ticket"}) {
			err = errors.New("NOTIFY_MATCHMAKER_PLAYER_LEFT bad input parameters")
			return err
		}

		if _, ok := m["exit_data"]; ok {
			contains_exit_data = true
		}
	}

	err := json.Unmarshal(message, &r)
	if err != nil {
		return err
	}

	valid := false
	errorResponse := map[string]any{}

	lobbyId := r.Lobby_id

	var sessionId *string

	gss := gameservers.GetGameServer(lobbyId)

	if gss != nil {

		var errorStr string
		sessionId, errorStr = gameservers.NotifyMatchmakerPlayerLeft(lobbyId, r.Ticket)

		// gsie.Lock()
		// if player, ok := gsie.Players[r.Ticket]; ok {
		// 	sessionId = player.SessionId
		// 	delete(gsie.Players, r.Ticket)

		// 	if gsie.RoomPlayerCount[player.RoomId] == 0 {
		// 		panic("ERROR")
		// 	}
		// 	gsie.RoomPlayerCount[player.RoomId] -= 1
		// }
		// gsie.Unlock()

		if sessionId != nil {
			if errorStr != "" {
				panic(0)
			}

			var account bson.M
			{
				target := []string{"session_id", *sessionId}

				projection := "session_id account_name"
				account, err = database.ReadAccount(target, projection)
				if err != nil {
					return err
				}
			}

			if account != nil {

				if contains_exit_data {
					// Trata la informacion que llega en exit_data

					if account_name, ok := account["account_name"]; ok {
						d := accountRaceTerminatedData{
							Guest:         r.Exit_data["guest"].(bool),
							Score:         uint(r.Exit_data["score"].(float64)),
							Race_time:     uint(r.Exit_data["race_time"].(float64)),
							Best_lap_time: uint(r.Exit_data["best_lap_time"].(float64)),
							Map_name:      r.Exit_data["map_name"].(string),
						}

						err := _process_race_terminated_data(account_name.(string), d, gss.GameName)
						if err != nil {
							return err
						}
						valid = true
					} else {
						errorResponse["error"] = "Account has no account name."
					}
				} else {
					valid = true
				}

				if valid {
					var response []byte
					response, err = json.Marshal(map[string]any{
						"request_id": r.Request_id,
						"lobby_id":   lobbyId,
						"session_id": sessionId,
					})
					if err != nil {
						return err
					}
					sendResponse(response)
				}
			} else {
				errorResponse["error"] = "No account found with this session_id."
			}
		} else {
			errorResponse["error"] = errorStr
		}
	} else {
		errorResponse["error"] = "Game server not found."
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
