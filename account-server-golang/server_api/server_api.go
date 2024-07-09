package server_api

import (
	"account-server/database"
	"account-server/ranking"
	"account-server/resource_manager"
	"account-server/utils"
	"encoding/json"

	"go.mongodb.org/mongo-driver/bson"
)

type dict = map[string]any

type accountRaceTerminatedData struct {
	Guest         bool
	Score         uint
	Race_time     uint
	Best_lap_time uint
	Map_name      string
}

func _process_race_terminated_data(ac_id string, d accountRaceTerminatedData, gameName string) error {
	is_guest := d.Guest

	var target []string
	var projection string
	if is_guest {
		target = []string{"guest_account_id", ac_id}
		projection = "guest_account_id display_name player_readonly_data player_data"
	} else {
		target = []string{"account_name", ac_id}
		projection = "account_name display_name player_readonly_data player_data"
	}

	var account dict

	// Obtiene la cuenta
	{
		responseDict, err := database.ReadAccount(target, projection)
		if err != nil {
			return err
		}
		account = responseDict
	}

	if account == nil {
		panic(0)
	}

	data_dict := dict{} // El dict que se utilizara para hacer el merge con lo que llega en r.Accounts

	var rod dict

	// Aqui se rellena data_dict con lo que hay en account["player_readonly_data"].
	{
		// ATENCION: Lo que hay en account["player_readonly_data"] es un str no un dict asi que hace falta convertirlo a dict.
		err := json.Unmarshal([]byte(account["player_readonly_data"].(string)), &rod)
		if err != nil {
			return err
		}
		if _, ok := rod["maps_data"]; !ok {
			// ATENCION: Las keys que son dict deben ya existir en 'player_readonly_data' antes de poder hacer un merge_leafs
			rod["maps_data"] = dict{}
		}
		data_dict["player_readonly_data"] = rod
	}

	gp := resource_manager.GetGameParameters(gameName)
	new_gold_value := int32(rod["gold"].(float64) + (float64(d.Score) * gp["RACE_GOLD_PER_POINT"].(float64)))

	// La entrada debe ser una lista de la forma [score, race_time, best_lap_time]
	// ATENCION: Tanto score como race_time o best_lap_time pueden ser 0, eso significa que no se les asigno ningun valor y no se deben tomar en cuenta.
	// update_list contendra los datos que han llegado desde el gameserver.
	update_list := []uint{d.Score, d.Race_time, d.Best_lap_time}
	update_dict := dict{"player_readonly_data": dict{"maps_data": dict{d.Map_name: update_list}, "gold": new_gold_value}}

	if maps_data, ok := rod["maps_data"]; ok { // Modifica update_dict y update_list segun lo que ya haya en la cuenta del player.
		if md, ok := maps_data.(dict)[d.Map_name]; ok {
			// Carga, en entry, los datos que hay actualmente en la cuenta del player.
			entry := md.([]any) // La entrada es una lista de la forma [score, race_time, best_lap_time]

			update_list[0] += uint(entry[0].(float64))

			// Si el tiempo que hay en la cuenta del player es mayor que 0
			// entonces modifica update_list[1] pero solo si lo que hay
			// en la cuenta mejora que lo que hay en update_list[1] o si update_list[1] es 0.
			if entry[1].(float64) > 0 {
				if uint(entry[1].(float64)) < update_list[1] || update_list[1] == 0 {
					update_list[1] = uint(entry[1].(float64))
				}
			}

			// Si el tiempo que hay en la cuenta del player es mayor que 0
			// entonces modifica update_list[2] pero solo si lo que hay
			// en la cuenta mejora que lo que hay en update_list[2] o si update_list[2] es 0.
			if entry[2].(float64) > 0 {
				if uint(entry[2].(float64)) < update_list[2] || update_list[2] == 0 {
					update_list[2] = uint(entry[2].(float64))
				}
			}
		}
	} else {
		panic(0)
	}

	utils.MergeDicts(data_dict, update_dict)

	// Update player_readonly_data
	{
		update := bson.D{bson.E{}}
		{
			bytes, err := json.Marshal(data_dict["player_readonly_data"])
			if err != nil {
				return err
			}
			update[0] = bson.E{Key: "player_readonly_data", Value: string(bytes)}
		}

		err := database.UpdateAccount(target, update)
		if err != nil {
			panic(0)
		}

		// Notifica al ranking que los datos de una account han cambiado
		{
			ranking.OnAccountUpdated(dict{
				"is_guest":             is_guest,
				"account_id":           ac_id,
				"display_name":         account["display_name"].(string),
				"player_data":          account["player_data"].(string),
				"player_readonly_data": update[0].Value,
			})
		}
	}

	return nil
}
