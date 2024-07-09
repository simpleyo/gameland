package server_api

import (
	"account-server/database"
	"account-server/utils"
	"encoding/json"
	"errors"
	"time"
)

type request_GET_GAME_RESOURCE struct {
	Request_id    string
	Session_id    string
	Game_name     string
	Resource_path string
	Resource_md5  string
}

// GET_GAME_RESOURCE
// 1. El cliente envia GET_GAME_RESOURCE(session_id) al servidor.
// 2. El servidor comprueba que existe esa session_id y no esta caducada.
// 3. El servidor responde con el resource o con error.
func GET_GAME_RESOURCE(message []byte, sendResponse func([]byte), sendBlob func([]byte)) error {

	var r request_GET_GAME_RESOURCE

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "session_id", "game_name", "resource_path", "resource_md5"}) {
			err = errors.New("GET_GAME_RESOURCE bad input parameters")
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

			err = internal_GET_RESOURCE(r.Request_id, r.Game_name, r.Resource_path, r.Resource_md5, sendResponse, sendBlob)
			return err

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
