package database

import (
	"strings"

	"go.mongodb.org/mongo-driver/bson"
)

type dict = map[string]any

// Crea una cuenta de guest y devuelve la respuesta como dict.
// A las cuentas guest no les afecta el <session_expire>.
func CreateGuestAccount(guestAccountId string, ip string) (dict, error) {
	return mongoCreateGuestAccount(guestAccountId, ip)
}

// Crea una cuenta y devuelve la respuesta como dict.
func CreateAccount(accountName string, displayName string, email string, keyHash string, ip string) (dict, error) {
	return mongoCreateAccount(accountName, displayName, email, keyHash, ip)
}

func ReadAllAccounts() ([]dict, error) {
	return mongoReadAllAccounts()
}

// Obtiene informacion de una cuenta y devuelve la respuesta como dict. Tambien permite
// comprobar si una cuenta existe.
// Devuelve dict=nil si no se ha encontrado la cuenta especificada.
func ReadAccount(target []string, projectionStr string) (dict, error) {
	if len(target) != 2 {
		panic(0)
	}

	query := bson.D{{Key: target[0], Value: target[1]}}
	projection := make(bson.D, 0, 32)
	p := strings.Split(projectionStr, " ")
	for _, v := range p {
		projection = append(projection, bson.E{Key: v, Value: true})
	}

	return mongoReadAccount(query, projection)
}

// Modifica informacion de una cuenta y devuelve la respuesta como dict.
// La no existencia de la cuenta es considerada como un error.
// No permite la insercion de nuevas keys en la account.
func UpdateAccount(target []string, update bson.D) error {
	if len(target) != 2 {
		panic(0)
	}

	mongo_query := bson.D{{Key: target[0], Value: target[1]}}
	mongo_update := bson.D{
		{Key: "$set", Value: update},
	}

	return mongoUpdateAccount(mongo_query, mongo_update)
}

func CreateOrder(orderMap dict) (int64, error) {
	data := bson.D{}
	for k, v := range orderMap {
		data = append(data, bson.E{Key: k, Value: v})
	}

	orderId := mongoGetNewOrderId()

	data = append(data, bson.E{Key: "_id", Value: orderId})

	return orderId, mongoCreateOrder(data)
}

func UpdateOrder(orderId int64, updateDict dict) error {
	mongo_query := bson.D{{Key: "_id", Value: orderId}}
	update := make(bson.D, 0, 8)
	for k, v := range updateDict {
		update = append(update, bson.E{Key: k, Value: v})
	}
	mongo_update := bson.D{
		{Key: "$set", Value: update},
	}
	return mongoUpdateOrder(mongo_query, mongo_update)
}

// Obtiene informacion de una order y devuelve la respuesta como dict. Tambien permite
// comprobar si una order existe.
// Devuelve dict=nil si no se ha encontrado la order especificada.
func ReadOrder(target []any) (dict, error) {
	if len(target) != 2 {
		panic(0)
	}

	query := bson.D{{Key: target[0].(string), Value: target[1]}}

	return mongoReadOrder(query)
}
