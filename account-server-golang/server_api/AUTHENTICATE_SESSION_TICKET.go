package server_api

import (
	"account-server/database"
	"account-server/utils"
	"encoding/json"
	"errors"
	"time"
)

type request_AUTHENTICATE_SESSION_TICKET struct {
	Request_id string
	Session_id string
}

// AUTHENTICATE_SESSION_TICKET:
// 1. Validated a client's session ticket, and if successful, returns details for that user
func AUTHENTICATE_SESSION_TICKET(message []byte, sendResponse func([]byte)) error {

	var r request_AUTHENTICATE_SESSION_TICKET

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "session_id"}) {
			err = errors.New("AUTHENTICATE_SESSION_TICKET bad input parameters")
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
		responseDict, err := database.ReadAccount(target, database.ACCOUNT_PROJECTION)
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
			responseDict = account
		} else {
			responseDict["error"] = "Session is expired."
		}

	} else {
		responseDict["error"] = "No account found with this session_id."
	}

	// Envia la respuesta

	responseDict["request_id"] = r.Request_id
	delete(responseDict, "account_salt")
	delete(responseDict, "account_hash")

	response, err := json.Marshal(responseDict)
	if err != nil {
		return err
	}
	sendResponse(response)

	return nil
}
