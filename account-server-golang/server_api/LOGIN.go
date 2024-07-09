package server_api

import (
	"account-server/database"
	"account-server/ranking"
	"account-server/utils"
	"crypto/md5"
	"encoding/json"
	"errors"
	"strings"
	"time"

	"github.com/gofiber/websocket/v2"
	"go.mongodb.org/mongo-driver/bson"
)

type request_LOGIN struct {
	Request_id     string
	Account_name   string
	Display_name   string
	Email          string
	Create_account bool
	Key_hash       string
}

// LOGIN
// 1. El cliente calcula key_hash = hash(password + hash(account_name))
// 2. El cliente envia LOGIN(account_name, display_name, key_hash) al servidor.
// 3. El servidor comprueba que existe una cuenta con el account_name. Si no existe entonces la crea.
// 4. El servidor comprueba que account_hash == hashmd5(key_hash + account_salt) y si no es correcto entonces devuelve error.
// 5. El servidor envia al cliente el session_id y los datos del player.
func LOGIN(message []byte, sendResponse func([]byte), c *websocket.Conn, create_account_allowed bool) error {

	var r request_LOGIN

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "account_name", "display_name", "create_account", "key_hash"}) {
			err = errors.New("LOGIN bad input parameters")
			return err
		}

		// Evita que las requests, que indican require_test_instance, se ejecuten en una instancia del account server que no es de test.
		if _, ok := m["require_test_instance"]; ok {
			if !database.IsTestInstance() {
				return errors.New("require_test_instance")
			}
		}

		// Evita que los clientes puedan crear cuentas con una request LOGIN. Deben utilizar REGISTER_ACCOUNT.
		{
			if r.Create_account && !create_account_allowed {
				response, err := json.Marshal(dict{
					"error": "Create account not allowed.",
				})
				if err != nil {
					return err
				}
				sendResponse(response)
				return nil
			}
		}
	}

	err := json.Unmarshal(message, &r)
	if err != nil {
		return err
	}

	accountName := strings.ToLower(r.Account_name) // Asegura que el nombre de la cuenta estara en minusculas.

	var account dict

	// Comprueba si existe una cuenta con el mismo nombre.
	{
		target := []string{"account_name", accountName}

		responseDict, err := database.ReadAccount(target, database.ACCOUNT_PROJECTION)
		if err != nil {
			return err
		}
		account = responseDict
	}

	if account == nil { // Si no hay una cuenta con ese nombre.
		if r.Create_account {

			remoteAddr := c.Conn.RemoteAddr().String()
			ip := remoteAddr[:strings.Index(remoteAddr, ":")]

			account, err = database.CreateAccount(accountName, r.Display_name, r.Email, r.Key_hash, ip)
			if err != nil {
				return err
			}

			// Notifica al ranking que se ha creado una nueva account
			{
				ranking.OnAccountUpdated(dict{
					"is_guest":             false,
					"account_id":           account["account_name"].(string),
					"display_name":         account["display_name"].(string),
					"player_data":          account["player_data"].(string),
					"player_readonly_data": account["player_readonly_data"].(string),
				})
			}
		} else {
			response, err := json.Marshal(dict{
				"error": "Account do not exist.",
			})
			if err != nil {
				return err
			}
			sendResponse(response)
			return nil
		}
	} else {
		if r.Create_account {
			response, err := json.Marshal(dict{
				"error": "Account name already exist.",
			})
			if err != nil {
				return err
			}
			sendResponse(response)
			return nil
		}

		// Actualiza la fecha de caducidad de la session de esta cuenta.
		{
			target := []string{"account_name", accountName}
			update := bson.D{{Key: "session_expire", Value: time.Now().Add(database.ACCOUNT_SESSION_EXPIRE_TIME).Format(time.RFC3339)}}

			err = database.UpdateAccount(target, update)
			if err != nil {
				panic(0)
			}

			for i := range update {
				pu := &update[i]
				account[pu.Key] = pu.Value
			}
		}
	}

	var responseDict dict

	// Comprueba que account_hash = hash(account_salt + key_hash).
	{
		keyHash := r.Key_hash
		var (
			accountSalt string
			accountHash string
		)
		if v, ok := account["account_salt"]; ok {
			accountSalt = v.(string)
			delete(account, "account_salt")
		}
		if v, ok := account["account_hash"]; ok {
			accountHash = v.(string)
			delete(account, "account_hash")
		}

		if accountHash == utils.Md5ToHexString(md5.Sum([]byte(keyHash+accountSalt))) {
			responseDict = account
		} else {
			responseDict = dict{}
			responseDict["error"] = "Invalid password."
		}
	}

	// Envia la respuesta

	responseDict["request_id"] = r.Request_id
	// delete(responseDict, "guest_account_id")

	response, err := json.Marshal(responseDict)
	if err != nil {
		return err
	}
	sendResponse(response)

	return nil
}
