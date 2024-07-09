package server_api

import (
	"account-server/database"
	"account-server/resource_manager"
	"account-server/utils"
	"encoding/json"
	"errors"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"golang.org/x/exp/slices"
)

type request_BUY_WITH_GOLD struct {
	Request_id string
	Session_id string
	Game_name  string
	Item_type  string
	Item_id    uint
}

// BUY_WITH_GOLD
// 1. El cliente envia BUY_WITH_GOLD(session_id) al servidor.
// 2. El servidor comprueba que existe esa session_id y no esta caducada.
// 3. El servidor responde con el resource o con error.
func BUY_WITH_GOLD(message []byte, sendResponse func([]byte)) error {

	var r request_BUY_WITH_GOLD

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "session_id", "game_name", "item_type", "item_id"}) {
			err = errors.New("BUY_WITH_GOLD bad input parameters")
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
		responseDict, err := database.ReadAccount(target, "guest_account_id session_expire player_readonly_data")
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

			if r.Game_name == "tanks" {

				game_parameters := resource_manager.GetGame("tanks")["GAME_PARAMETERS"].(dict)

				if r.Item_type == "skin" { // SKIN
					max_number_of_skins := uint(game_parameters["MAX_NUMBER_OF_SKINS"].(float64))
					if r.Item_id < max_number_of_skins {
						var rod dict
						err := json.Unmarshal([]byte(account["player_readonly_data"].(string)), &rod)
						if err != nil {
							return err
						}
						skin_ids := rod["skin_ids"].([]any)
						gold_total := rod["gold"].(float64)
						value := game_parameters["SKIN_PRICES"].([]any)[r.Item_id].(float64)
						if value <= gold_total {
							if slices.IndexFunc(skin_ids, func(skin_id any) bool { return uint(skin_id.(float64)) == r.Item_id }) < 0 {
								rod["gold"] = gold_total - value
								rod["skin_ids"] = append(skin_ids, r.Item_id)

								target := []string{"session_id", r.Session_id}
								update := bson.D{bson.E{}}
								{
									bytes, err := json.Marshal(rod)
									if err != nil {
										return err
									}
									update[0] = bson.E{Key: "player_readonly_data", Value: string(bytes)}
								}
								// projection := "session_id player_readonly_data"

								err := database.UpdateAccount(target, update)
								if err == nil {
									responseDict["session_id"] = r.Session_id
									responseDict["player_readonly_data"] = update[0].Value
								} else {
									responseDict["error"] = "There was a problem updating the account."
								}
							} else {
								responseDict["error"] = "You already own that item.\nYou do not need to buy it again."
							}
						} else {
							responseDict["error"] = "Could not buy.\nYou do not have enough gold."
						}
					} else {
						responseDict["error"] = "Item id out of bounds"
					}
				} else if r.Item_type == "flag" { // FLAG
					max_number_of_flags := uint(game_parameters["MAX_NUMBER_OF_FLAGS"].(float64))
					if r.Item_id < max_number_of_flags {
						var rod dict
						err := json.Unmarshal([]byte(account["player_readonly_data"].(string)), &rod)
						if err != nil {
							return err
						}
						flag_ids := rod["flag_ids"].([]any)
						gold_total := rod["gold"].(float64)
						value := game_parameters["FLAG_PRICE"].(float64)
						if value <= gold_total {
							if slices.IndexFunc(flag_ids, func(flag_id any) bool { return uint(flag_id.(float64)) == r.Item_id }) < 0 {
								rod["gold"] = gold_total - value
								rod["flag_ids"] = append(flag_ids, r.Item_id)

								target := []string{"session_id", r.Session_id}
								update := bson.D{bson.E{}}
								{
									bytes, err := json.Marshal(rod)
									if err != nil {
										return err
									}
									update[0] = bson.E{Key: "player_readonly_data", Value: string(bytes)}
								}
								// projection := "session_id player_readonly_data"

								err := database.UpdateAccount(target, update)
								if err == nil {
									responseDict["session_id"] = r.Session_id
									responseDict["player_readonly_data"] = update[0].Value
								} else {
									responseDict["error"] = "There was a problem updating the account."
								}
							} else {
								responseDict["error"] = "You already own that item.\nYou do not need to buy it again."
							}
						} else {
							responseDict["error"] = "Could not buy.\nYou do not have enough gold."
						}
					} else {
						responseDict["error"] = "Item id out of bounds"
					}
				} else {
					responseDict["error"] = "Item type not valid."
				}
			} else {
				responseDict["error"] = "Game not valid."
			}
		} else {
			responseDict["error"] = "Session is expired."
		}
	} else {
		responseDict["error"] = "No account found with this session_id."
	}

	// Envia la respuesta

	responseDict["request_id"] = r.Request_id
	delete(responseDict, "guest_account_id")

	response, err := json.Marshal(responseDict)
	if err != nil {
		return err
	}
	sendResponse(response)

	return nil
}
