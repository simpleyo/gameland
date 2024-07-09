package server_api

import (
	"account-server/database"
	"account-server/utils"
	"encoding/json"
	"errors"
	"time"

	"go.mongodb.org/mongo-driver/bson"
)

type request_PUT_COMMENT struct {
	Request_id string
	Session_id string
	Comment    string
}

func PUT_COMMENT(message []byte, sendResponse func([]byte)) error {

	var r request_PUT_COMMENT

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "session_id", "comment"}) {
			err = errors.New("PUT_COMMENT bad input parameters")
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
		responseDict, err := database.ReadAccount(target, "guest_account_id session_id comments")
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

			// Update comments
			{
				comments := ""
				if v, ok := account["comments"]; ok {
					comments = v.(string)
				}

				new_comments := comments + "\n\n\n" + time.Now().String() + "\n" + r.Comment
				// Limita el tamaño de new_comments, implementando algo parecido a un buffer circular.
				{
					MAX_COMMENTS_SIZE := 64 * 1024 // En bytes
					if len(new_comments) >= MAX_COMMENTS_SIZE {
						new_comments = new_comments[MAX_COMMENTS_SIZE/2:]
					}
				}

				target := []string{"session_id", r.Session_id}
				update := bson.D{}
				update = append(update, bson.E{Key: "comments", Value: comments + "\n\n\n" + time.Now().String() + "\n" + r.Comment})

				err = database.UpdateAccount(target, update)
				if err != nil {
					panic(0)
				}

				responseDict = dict{
					"session_id": r.Session_id,
				}
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
