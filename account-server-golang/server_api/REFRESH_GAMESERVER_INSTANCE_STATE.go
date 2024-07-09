package server_api

import (
	"account-server/gameservers"
	"account-server/utils"
	"encoding/json"
	"errors"
)

type request_REFRESH_GAMESERVER_INSTANCE_STATE struct {
	Request_id  string
	Lobby_id    string
	Current_map string
}

//REFRESH_GAMESERVER_INSTANCE_STATE:
// 1. El controller (del gameserver node) envia el lobby_id.
// 2. El servidor actualiza el estado de la instancia en la lista de gameserver instances.
//    Si no existe el lobby_id en la lista de los game servers entonces devuelve lobby_id vacio.
func REFRESH_GAMESERVER_INSTANCE_STATE(message []byte, sendResponse func([]byte)) error {

	var r request_REFRESH_GAMESERVER_INSTANCE_STATE

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "lobby_id", "current_map"}) {
			err = errors.New("REFRESH_GAMESERVER_INSTANCE_STATE bad input parameters")
			return err
		}
	}

	err := json.Unmarshal(message, &r)
	if err != nil {
		return err
	}

	lobbyId := r.Lobby_id
	ok := gameservers.RefreshGameServer(lobbyId, r.Current_map)
	if !ok {
		lobbyId = ""
	}

	response, err := json.Marshal(map[string]any{
		"request_id": r.Request_id,
		"lobby_id":   lobbyId,
	})

	if err != nil {
		return err
	}

	// fmt.Println("Enviada respuesta para REFRESH_GAMESERVER_INSTANCE_STATE request_id: ", r.Request_id)
	sendResponse(response)

	return err
}
