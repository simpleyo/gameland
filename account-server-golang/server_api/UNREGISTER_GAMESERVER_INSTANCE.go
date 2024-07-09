package server_api

import (
	"account-server/gameservers"
	"account-server/utils"
	"encoding/json"
	"errors"
)

type request_UNREGISTER_GAMESERVER_INSTANCE struct {
	Request_id string
	Lobby_id   string
}

// UNREGISTER_GAMESERVER_INSTANCE:
// 1. El controller (del gameserver node) envia el lobby_id.
// 2. El servidor elimina la entrada con lobby_id de la lista de gameserver instances.
func UNREGISTER_GAMESERVER_INSTANCE(message []byte, sendResponse func([]byte)) error {

	var r request_UNREGISTER_GAMESERVER_INSTANCE

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "lobby_id"}) {
			err = errors.New("UNREGISTER_GAMESERVER_INSTANCE bad input parameters")
			return err
		}
	}

	err := json.Unmarshal(message, &r)
	if err != nil {
		return err
	}

	gameservers.RemoveGameServer(r.Lobby_id)

	response, err := json.Marshal(map[string]any{
		"request_id": r.Request_id,
		"lobby_id":   r.Lobby_id,
	})

	if err != nil {
		return err
	}

	sendResponse(response)

	return err
}
