package server_api

import (
	"account-server/database"
	"account-server/gameservers"
	"account-server/resource_manager"
	"account-server/utils"
	"encoding/json"
	"errors"
	"time"
)

type request_MATCHMAKE struct {
	Request_id                string
	Session_id                string
	Game_name                 string
	Preferred_region          string
	Preferred_lobby_id        string
	Preferred_room_tag        string
	Game_client_resources_md5 string
}

// MATCHMAKE:
// 1. Busca un slot disponible en un gameserver y devuelve el ticket al cliente.
func MATCHMAKE(message []byte, sendResponse func([]byte)) error {

	var r request_MATCHMAKE

	opt_preferred_room_tag := "" // Parametro opcional (con valor por defecto "") para request_MATCHMAKE

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "session_id", "game_name", "preferred_region", "preferred_lobby_id", "game_client_resources_md5"}) {
			err = errors.New("MATCHMAKE bad input parameters")
			return err
		}

		if _, ok := m["require_test_instance"]; ok { // Evita que las requests, que indican require_test_instance, se ejecuten en una instancia del account server que no es de test.
			if !database.IsTestInstance() {
				return errors.New("require_test_instance")
			}
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

			ticket, lobbyId := gameservers.MatchMake(r.Game_name, r.Preferred_region, r.Preferred_lobby_id, r.Preferred_room_tag, r.Session_id)

			// Si hay ticket entonces lo envia al cliente.
			if ticket != "" {
				if lobbyId == "" {
					panic(0)
				}

				gss := gameservers.GetGameServer(lobbyId)
				if gss != nil {
					responseDict["ticket"] = ticket

					game_map_names := make([]string, 0, 32)
					for _, k := range resource_manager.GetGameEnabledMaps(r.Game_name) {
						game_map_names = append(game_map_names, k.(string))
					}

					game_client_resources_md5 := resource_manager.GetGameClientResourcesMd5(r.Game_name)

					gs_info := dict{
						"lobby_id":                  gss.Lobby_id,
						"build_id":                  gss.Build_id,
						"ipv4_address":              gss.Ipv4_address,
						"address":                   gss.Address,
						"port":                      gss.Port,
						"region":                    gss.Region,
						"player_count":              gss.PlayerCount,
						"max_rooms":                 gss.Max_rooms,
						"max_players_per_room":      gss.Max_players_per_room,
						"game_name":                 gss.GameName,
						"game_client_resources_md5": game_client_resources_md5,
						"game_map_names":            game_map_names, // Nombres de todos los mapas del juego que estan listados en la entrada "ENABLED_MAPS" en el fichero game.cfg.
					}

					if game_client_resources_md5 != r.Game_client_resources_md5 {
						gs_info["game_client_resources"] = resource_manager.GetGameClientResources(r.Game_name)
					}

					responseDict["session_id"] = r.Session_id
					responseDict["gameserver_info"] = gs_info
					responseDict["request_id"] = r.Request_id
				} else {
					responseDict["error"] = "Gameserver no longer exists."
				}
			} else {
				responseDict["error"] = "All game servers are busy."
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
