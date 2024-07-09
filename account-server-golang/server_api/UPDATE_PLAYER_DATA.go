package server_api

import (
	"account-server/database"
	"account-server/ranking"
	"account-server/utils"
	"encoding/json"
	"errors"
	"time"

	"go.mongodb.org/mongo-driver/bson"
)

type request_UPDATE_PLAYER_DATA struct {
	Request_id   string
	Session_id   string
	Display_name string
	Player_data  string
}

// UPDATE_PLAYER_DATA:
// 1. Validated a client's session ticket, and if successful, returns details for that user
func UPDATE_PLAYER_DATA(message []byte, sendResponse func([]byte)) error {

	var r request_UPDATE_PLAYER_DATA

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "session_id"}) {
			err = errors.New("UPDATE_PLAYER_DATA bad input parameters")
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
		responseDict, err := database.ReadAccount(target, "guest_account_id account_name session_id session_expire display_name player_data player_readonly_data")
		if err != nil {
			return err
		}
		account = responseDict
	}

	responseDict := dict{}

	if account != nil {

		sessionExpired := false

		var guestAccountId string
		if v, ok := account["guest_account_id"]; ok {
			guestAccountId = v.(string)
		}
		is_guest := (guestAccountId != "")

		if is_guest {
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

			// Update player_data
			{
				actual_display_name := account["display_name"].(string)
				actual_player_data := account["player_data"].(string)
				new_display_name := utils.CropString(r.Display_name, 16)
				new_player_data := r.Player_data

				if (actual_display_name != new_display_name) || (actual_player_data != new_player_data) {
					target := []string{"session_id", r.Session_id}
					update := bson.D{}
					if r.Display_name != "" {
						update = append(update, bson.E{Key: "display_name", Value: new_display_name})
					}
					if r.Player_data != "" {
						update = append(update, bson.E{Key: "player_data", Value: new_player_data})
					}

					err = database.UpdateAccount(target, update)
					if err != nil {
						panic(0)
					}

					for i := range update {
						pu := &update[i]
						account[pu.Key] = pu.Value
					}

					// Notifica al ranking que los datos de una account han cambiado
					{
						account_id := guestAccountId
						if !is_guest {
							account_id = account["account_name"].(string)
						}

						ranking.OnAccountUpdated(dict{
							"is_guest":             is_guest,
							"account_id":           account_id,
							"display_name":         account["display_name"].(string),
							"player_data":          account["player_data"].(string),
							"player_readonly_data": account["player_readonly_data"].(string),
						})
					}
				}

				responseDict = account
			}

		} else {
			responseDict["error"] = "Session is expired."
		}

	} else {
		responseDict["error"] = "No account found with this session_id."
	}

	// Envia la respuesta

	responseDict["request_id"] = r.Request_id
	// delete(account, "guest_account_id")
	// delete(account, "session_expire")

	response, err := json.Marshal(responseDict)
	if err != nil {
		return err
	}
	sendResponse(response)

	return nil
}
