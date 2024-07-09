package server_api

import (
	"account-server/database"
	"account-server/gameservers"
	"account-server/utils"
	"encoding/json"
	"errors"
	"fmt"
	"time"
)

type request_READ_GAME_SERVERS struct {
	Request_id string
	Session_id string
}

func READ_GAME_SERVERS(message []byte, sendResponse func([]byte)) error {

	var r request_READ_GAME_SERVERS

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "session_id"}) {
			err = errors.New("READ_GAME_SERVERS bad input parameters")
			return err
		}

		if _, ok := m["require_test_instance"]; ok { // Evita que las requests, que indican require_test_instance, se ejecuten en una instancia del account server que no es de test.
			if !database.IsTestInstance() {
				return errors.New("require_test_instance")
			}
		}
	}

	err := json.Unmarshal(message, &r)
	if err != nil {
		return err
	}

	var account dict

	// Comprueba si existe una cuenta con esa session_id
	{
		target := []string{"session_id", r.Session_id}
		responseDict, err := database.ReadAccount(target, "session_expire guest_account_id")
		if err != nil {
			return err
		}
		account = responseDict
	}

	responseDict := dict{}

	if account != nil {

		sessionExpired := false

		if account["guest_account_id"] != nil {
			// Para las cuentas guest no se aplica session_expire
		} else {
			// Comprueba que la session no esta caducada
			expireTimeStr := account["session_expire"].(string) // Sera "" si session_expire no esta en account
			if expireTimeStr == "" {
				panic(0)
			}
			expireTime, err := time.Parse(time.RFC3339, expireTimeStr)
			if err != nil {
				panic(0)
			}
			sessionExpired = expireTime.Before(time.Now())
		}

		if !sessionExpired {

			// Read game servers
			{
				gservers := gameservers.GetGameServers()

				gameServersInfoList := []dict{}
				for _, gsie := range gservers {
					gameServersInfoList = append(gameServersInfoList, dict{
						"lobby_id":             gsie.Lobby_id,
						"server_name":          gsie.Server_name,
						"ipv4_address":         gsie.Ipv4_address + ":" + fmt.Sprint(gsie.Port),
						"address":              gsie.Address + ":" + fmt.Sprint(gsie.Port),
						"region":               gsie.Region,
						"player_count":         gsie.PlayerCount,
						"max_player_count":     gsie.Max_rooms * gsie.Max_players_per_room,
						"max_rooms":            gsie.Max_rooms,
						"max_players_per_room": gsie.Max_players_per_room,
						"game":                 dict{"game_name": gsie.GameName, "map_name": gsie.MapName},
						// "per_room_player_count": gsie.RoomPlayerCount,
					})
				}

				responseDict["session_id"] = r.Session_id
				responseDict["game_servers"] = gameServersInfoList
			}

		} else {
			responseDict["error"] = "Session is expired."
		}

	} else {
		responseDict["error"] = "No account found with this session_id."
	}

	// Envia la respuesta

	responseDict["request_id"] = r.Request_id

	response, err := json.Marshal(responseDict)
	if err != nil {
		return err
	}
	sendResponse(response)

	return nil
}
