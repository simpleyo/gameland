package server_api

import (
	"account-server/database"
	"account-server/ranking"
	"account-server/utils"
	"encoding/json"
	"errors"
	"strings"

	"github.com/gofiber/websocket/v2"
)

type request_LOGIN_AS_GUEST struct {
	Request_id       string
	Guest_account_id string
}

// LOGIN_AS_GUEST:
//  - El cliente envia guest_account_id (generado aleatoriamente) y display_name.
//  - Si no existe guest_account_id entonces el servidor crea (createAccount) una nueva cuenta, con una caducidad para session_id de 180 dias.
//  - Si existe el guest_account_id, la caducidad de la sesion se actualiza a 180 dias.
//  - El servidor responde al cliente con un session_id.
//  - El cliente guardara el guest_account_id y el session_id el cual tiene fecha de caducidad.
//  - El cliente, con el session_id, puede hacer peticiones al servidor (getPlayerData) hasta que el
//    servidor responda con error de sesion caducada. Entonces el cliente debera utilizar el guest_account_id para
//    volver a hacer login.
//  - El cliente se considera a si mismo logueado si tiene una session_id no caducada, es decir, para la cual el servidor no ha respondido con error.
//  - En la misma llamada de login se devuelve la "player data"
func LOGIN_AS_GUEST(message []byte, sendResponse func([]byte), c *websocket.Conn) error {

	var r request_LOGIN_AS_GUEST

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "guest_account_id"}) {
			err = errors.New("LOGIN_AS_GUEST bad input parameters")
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

	// Comprueba si existe una cuenta con el mismo guest_account_id.
	{
		target := []string{"guest_account_id", r.Guest_account_id}

		responseDict, err := database.ReadAccount(target, database.ACCOUNT_PROJECTION)
		if err != nil {
			return err
		}
		account = responseDict
	}

	if account == nil { // Si no hay una cuenta con ese nombre.

		remoteAddr := c.Conn.RemoteAddr().String()
		ip := remoteAddr[:strings.Index(remoteAddr, ":")]

		responseDict, err := database.CreateGuestAccount(r.Guest_account_id, ip)
		if err != nil {
			responseDict["error"] = err.Error()
		}
		account = responseDict

		// Notifica al ranking que se ha creado una nueva account
		{
			ranking.OnAccountUpdated(dict{
				"is_guest":             true,
				"account_id":           account["guest_account_id"].(string),
				"display_name":         account["display_name"].(string),
				"player_data":          account["player_data"].(string),
				"player_readonly_data": account["player_readonly_data"].(string),
			})
		}
	}

	responseDict := account
	responseDict["request_id"] = r.Request_id

	response, err := json.Marshal(responseDict)

	if err != nil {
		return err
	}

	sendResponse(response)

	return err
}
