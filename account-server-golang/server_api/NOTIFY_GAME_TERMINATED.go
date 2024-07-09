package server_api

import (
	"account-server/gameservers"
	"account-server/utils"
	"encoding/json"
	"errors"
)

type request_NOTIFY_GAME_TERMINATED struct {
	Request_id string
	Lobby_id   string
	Game_name  string
	Map_name   string
	Accounts   map[string]([]any) // Mapa indexado por account_name o guest_account_id, los valores son listas con formato [guest(bool), score, race_time, best_lap_time]
}

// NOTIFY_GAME_TERMINATED:
// 1. Validates a Game Server session ticket and returns details about the user
func NOTIFY_GAME_TERMINATED(message []byte, sendResponse func([]byte)) error {

	var r request_NOTIFY_GAME_TERMINATED

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "lobby_id", "game_name", "map_name", "accounts"}) {
			err = errors.New("NOTIFY_GAME_TERMINATED bad input parameters")
			return err
		}
	}

	err := json.Unmarshal(message, &r)
	if err != nil {
		return err
	}

	valid := false
	errorResponse := map[string]any{}

	if ok := gameservers.ExistGameServer(r.Lobby_id); ok {

		for ac_id, ac_value := range r.Accounts {

			d := accountRaceTerminatedData{
				Guest:         ac_value[0].(bool),
				Score:         uint(ac_value[1].(float64)),
				Race_time:     uint(ac_value[2].(float64)),
				Best_lap_time: uint(ac_value[3].(float64)),
				Map_name:      r.Map_name,
			}

			err := _process_race_terminated_data(ac_id, d, r.Game_name)
			if err != nil {
				return err
			}
		}

		// Envia la respuesta
		{
			responseDict := dict{}
			responseDict["request_id"] = r.Request_id

			var response []byte
			response, err = json.Marshal(responseDict)
			if err != nil {
				return err
			}
			sendResponse(response)
			valid = true
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
