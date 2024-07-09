package orders

import (
	"account-server/database"
	"account-server/utils"
	"encoding/json"
	"fmt"
	"time"

	"go.mongodb.org/mongo-driver/bson"
)

type dict = map[string]any

type OrderParams struct {
	Account_name string
	Item_type    string
	Item_id      uint
	Value        float32
}

type payPalOrder struct {
	PaypalOrderId    string
	Date             string
	PaymentCompleted bool
	*OrderParams
}

func CreateOrder(orderParams *OrderParams) (int64, error) {
	po := payPalOrder{}
	po.OrderParams = orderParams
	po.Date = time.Now().Format(time.RFC3339)
	po.PaymentCompleted = false

	orderMap := dict{
		"PaypalOrderId":    po.PaypalOrderId,
		"Date":             po.Date,
		"PaymentCompleted": po.PaymentCompleted,
		"Account_name":     po.Account_name,
		"Item_type":        po.Item_type,
		"Item_id":          po.Item_id,
		"Value":            fmt.Sprintf("%.2f", po.Value),
	}

	return database.CreateOrder(orderMap)
}

func PaymentCanceledOrError(orderId int64, payPalOrderId string) error {
	if payPalOrderId != "" {
		update := dict{"PaypalOrderId": payPalOrderId, "OrderCanceled": true}
		return database.UpdateOrder(orderId, update)
	}
	return nil
}

func PaymentCompleted(orderId int64, payPalOrderId string) error {
	update := dict{"PaypalOrderId": payPalOrderId, "PaymentCompleted": true}
	err := database.UpdateOrder(orderId, update)
	if err != nil {
		return err
	}

	// Suma el oro a la cuenta si es necesario
	{
		gold := int64(0)
		account_name := ""

		// Obtiene el nombre de la cuenta y el gold asociado a la order OrderId
		{
			order, err := ReadOrder(orderId)
			if err != nil {
				return err
			}

			if order["Item_type"].(string) == "gold" {
				gold = order["Item_id"].(int64)
				account_name = order["Account_name"].(string)
			}
		}

		if account_name != "" && gold > 0 {
			// Aqui hay que incrementar el gold de la cuenta <account_name>.

			data_dict := dict{} // El dict que se utilizara para hacer el merge con lo que llegara en <player_readonly_data_update>
			var account dict

			// Comprueba que existe una cuenta con el account_name dado
			{
				target := []string{"account_name", account_name}

				projection := "player_readonly_data"
				ac, err := database.ReadAccount(target, projection)
				if err != nil {
					return err
				}
				account = ac
			}

			// Aqui se rellena data_dict con lo que hay en account["player_readonly_data"].
			{
				// ATENCION: Lo que hay en account["player_readonly_data"] es un str no un dict asi que hace falta convertirlo a dict.
				var undata dict
				err := json.Unmarshal([]byte(account["player_readonly_data"].(string)), &undata)
				if err != nil {
					return err
				}
				if _, ok := undata["maps_data"]; !ok {
					// ATENCION: Las keys que son dict deben ya existir en 'player_readonly_data' antes de poder hacer un merge_leafs
					undata["maps_data"] = dict{}
				}
				data_dict["player_readonly_data"] = undata
			}

			// Realiza el MergeDicts
			{
				player_readonly_data_update := dict{"player_readonly_data": dict{"gold": gold + int64(data_dict["player_readonly_data"].(dict)["gold"].(float64))}}
				utils.MergeDicts(data_dict, player_readonly_data_update)
			}

			// Update player_readonly_data
			{
				target := []string{"account_name", account_name}
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
					return err
				}
			}
		}
	}

	return nil
}

func ReadOrder(orderId int64) (dict, error) {
	target := []any{"_id", orderId}
	responseDict, err := database.ReadOrder(target)
	if err != nil {
		return nil, err
	}
	return responseDict, nil
}
