package server_api

import (
	"account-server/gameservers"
	"account-server/utils"
	"encoding/json"
	"errors"
)

type request_GET_GAMESERVER_RESOURCE struct {
	Request_id    string
	Lobby_id      string
	Game_name     string
	Resource_path string
	Resource_md5  string
}

// GET_GAMESERVER_RESOURCE:
// 1. El gameserver envia GET_GAMESERVER_RESOURCE('lobby_id', 'ticket') al servidor.
// 2. El servidor comprueba que existe esa session_id y no esta caducada.
// 3. El servidor responde con el resource o con error.
func GET_GAMESERVER_RESOURCE(message []byte, sendResponse func([]byte), sendBlob func([]byte)) error {

	var r request_GET_GAMESERVER_RESOURCE

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "lobby_id", "game_name", "resource_path", "resource_md5"}) {
			err = errors.New("GET_GAMESERVER_RESOURCE bad input parameters")
			return err
		}
	}

	err := json.Unmarshal(message, &r)
	if err != nil {
		return err
	}

	if ok := gameservers.ExistGameServer(r.Lobby_id); ok {
		err = internal_GET_RESOURCE(r.Request_id, r.Game_name, r.Resource_path, r.Resource_md5, sendResponse, sendBlob)
		if err != nil {
			return err
		}
	}

	return err
}
