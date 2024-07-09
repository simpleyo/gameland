package database

import (
	"account-server/utils"
	"context"
	"crypto/md5"
	"fmt"
	"math/rand"
	"strings"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

var global_client *mongo.Client
var accountsCollection *mongo.Collection
var ordersCollection *mongo.Collection
var sequentialIdCollection *mongo.Collection

const GAME_DATABASE_NAME = "carsgame"
const ACCOUNTS_COLLECTION_NAME = "accounts"
const ORDERS_COLLECTION_NAME = "orders"
const SEQUENTIAL_ID_COLLECTION_NAME = "sequential_id"

const ACCOUNT_PROJECTION = "account_info display_name player_data player_readonly_data guest_account_id account_name email email_validated creation_time session_id session_expire account_salt account_hash"
const ACCOUNT_SESSION_EXPIRE_TIME = 360 * (time.Hour * 24) // Tiempo que tarda en expirar una sesion desde que se hizo login.

var ACCOUNT_PROJECTION_SLICE []string = strings.Split(ACCOUNT_PROJECTION, " ")
var ACCOUNT_PROJECTION_MAP map[string]bool = func() map[string]bool {
	apm := make(map[string]bool)
	for _, v := range ACCOUNT_PROJECTION_SLICE {
		apm[v] = true
	}
	return apm
}()

var isTestInstance bool

var accountDefaults accountDefaultsStruct = accountDefaultsStruct{
	DISPLAY_NAME: "Player",
	ACCOUNT_INFO: "",
	// Los valores por defecto para PLAYER_DATA se definen al crear la cuenta. Ver DEFAULT_PLAYER_DATA.
	PLAYER_READONLY_DATA: `{ "gold": 0, "skin_ids": [0], "flag_ids": [], "maps_data": {} }`,
}

type Account struct {
	Guest_account_id     string // guest_account_id solo esta en las cuentas que son guest // @sparseindex @unique Es sparse porque pueden haber documentos que no contienen guest_account_id
	Account_name         string // account_name solo esta en las cuentas que no son guest // @sparseindex @unique
	Session_id           string // @index @unique
	Session_expire       string
	Display_name         string // Nombre que se muestra en el juego
	Player_data          string
	Player_readonly_data string
	Email                string // email y email_validated solo estan en las cuentas que no son guest // @sparseindex
	Email_validated      bool
	Creation_time        string
	Creation_ip          string
	Account_salt         string // account_salt y account_hash solo estan en las cuentas que no son guest
	Account_hash         string
	Account_info         string
}

type accountDefaultsStruct struct {
	DISPLAY_NAME         string
	ACCOUNT_INFO         string
	PLAYER_READONLY_DATA string
}

func Initialize(is_test_instance bool) {
	client, err := mongo.Connect(context.Background(), options.Client().ApplyURI("mongodb://localhost:27017"))
	if err != nil {
		panic(err)
	}

	global_client = client

	isTestInstance = is_test_instance

	var database *mongo.Database
	if isTestInstance {
		database = client.Database(GAME_DATABASE_NAME + "_test")
	} else {
		database = client.Database(GAME_DATABASE_NAME)
	}

	// Inicializa <accountsCollection>
	{
		accountsCollection = database.Collection(ACCOUNTS_COLLECTION_NAME)
		accCol := accountsCollection

		var model mongo.IndexModel
		model.Keys = bson.D{{Key: "account_name", Value: 1}}
		var indexOptions options.IndexOptions
		indexOptions.SetName("account_name_1")
		indexOptions.SetSparse(true)
		indexOptions.SetUnique(true)
		model.Options = &indexOptions

		_, err = accCol.Indexes().CreateOne(context.TODO(), model)
		if err != nil {
			panic(err)
		}

		indexOptions.SetName("guest_account_id")
		model.Keys = bson.D{{Key: "guest_account_id", Value: 1}}
		_, err = accCol.Indexes().CreateOne(context.TODO(), model)
		if err != nil {
			panic(err)
		}

		indexOptions.SetName("session_id")
		model.Keys = bson.D{{Key: "session_id", Value: 1}}
		_, err = accCol.Indexes().CreateOne(context.TODO(), model)
		if err != nil {
			panic(err)
		}
	}

	// Inicializa <ordersCollection>
	{
		ordersCollection = database.Collection(ORDERS_COLLECTION_NAME)
	}

	// Inicializa <sequentialIdCollection>
	{
		sequentialIdCollection = database.Collection(SEQUENTIAL_ID_COLLECTION_NAME)
		seqCol := sequentialIdCollection

		query := bson.D{{Key: "_id", Value: "order_id"}} // order_id es el id que se utilizara para la orders de paypal.
		// Inserta la entrada <order_id> en la coleccion <sequential_id> si no estaba ya insertada.
		{
			var result bson.M
			if err := seqCol.FindOne(context.Background(), query).Decode(&result); err != nil {
				if err == mongo.ErrNoDocuments {
					update := bson.D{
						{Key: "$set",
							Value: bson.D{
								{Key: "sequence_value", Value: int64(0)},
							},
						},
					}
					updateOptions := options.Update()
					updateOptions.SetUpsert(true)
					_, err := seqCol.UpdateOne(context.Background(), query, update, updateOptions)
					if err != nil {
						panic(0)
					}
				}
			}
		}
	}
}

func IsTestInstance() bool {
	return isTestInstance
}

func mongoReadAllAccounts() ([]dict, error) {
	cursor, err := accountsCollection.Find(context.Background(), bson.D{})
	if err != nil {
		return nil, err
	}

	var results []dict

	if err = cursor.All(context.Background(), &results); err != nil {
		return nil, err
	} else {
		return results, err
	}
}

func mongoCreateAccount(accountName string, displayName string, email string, keyHash string, ip string) (dict, error) {
	filter := bson.D{{Key: "account_name", Value: accountName}}

	accountSalt := utils.GenerateRandomString(32)
	accountHash := utils.Md5ToHexString(md5.Sum([]byte(keyHash + accountSalt)))

	if displayName == "" {
		displayName = accountDefaults.DISPLAY_NAME
	} else {
		displayName = utils.CropString(displayName, 16)
	}

	// ATENCION: No se debe incluir en <update> la key que se utiliza en <filter>.
	// Si se hace provoca que MongoDB indique un error de escritura por conflicto ya que
	// se estaria intentando actualizar la key que se esta utilizando como <filter>.

	DEFAULT_PLAYER_DATA := `{ "color_id":  ` + fmt.Sprintf("%d", rand.Int63()%21) + `, "skin_index": 0, "flag_index": -1 }`

	// Para desactivar el warning ejecutar el comando "go doc cmd/vet" en el Terminal.
	update := bson.D{
		{Key: "$set",
			Value: bson.D{
				{Key: "ip", Value: ip},
				{Key: "display_name", Value: displayName},
				{Key: "email", Value: email},
				{Key: "email_validated", Value: false},
				{Key: "account_salt", Value: accountSalt},
				{Key: "account_hash", Value: accountHash},
				{Key: "creation_time", Value: time.Now().Format(time.RFC3339)},
				{Key: "session_id", Value: utils.GenerateRandomString(32)},
				{Key: "session_expire", Value: time.Now().Add(ACCOUNT_SESSION_EXPIRE_TIME).Format(time.RFC3339)},
				{Key: "account_name", Value: accountName},
				{Key: "account_info", Value: accountDefaults.ACCOUNT_INFO},
				{Key: "player_data", Value: DEFAULT_PLAYER_DATA},
				{Key: "player_readonly_data", Value: accountDefaults.PLAYER_READONLY_DATA},
			},
		},
	}

	updateOptions := options.Update()
	updateOptions.SetUpsert(true)

	_, err := accountsCollection.UpdateOne(context.Background(), filter, update, updateOptions)
	if err != nil {
		return nil, err
	}

	result, ok := update[0].Value.(bson.D)
	if !ok {
		panic(0)
	}
	result = append(result, bson.E{Key: "account_name", Value: accountName})

	return result.Map(), err
}

func mongoCreateGuestAccount(guestAccountId string, ip string) (dict, error) {
	filter := bson.D{{Key: "guest_account_id", Value: guestAccountId}}

	// ATENCION: No se debe incluir en <update> la key que se utiliza en <filter>.
	// Si se hace provoca que MongoDB indique un error de escritura por conflicto ya que
	// se estaria intentando actualizar la key que se esta utilizando como <filter>.

	DEFAULT_PLAYER_DATA := `{ "color_id":  ` + fmt.Sprintf("%d", rand.Int63()%21) + `, "skin_index": 0, "flag_index": -1 }`

	// Para desactivar el warning ejecutar el comando "go doc cmd/vet" en el Terminal.
	update := bson.D{
		{Key: "$set",
			Value: bson.D{
				{Key: "ip", Value: ip},
				{Key: "creation_time", Value: time.Now().Format(time.RFC3339)},
				{Key: "session_id", Value: utils.GenerateRandomString(32)},
				{Key: "session_expire", Value: time.Now().Format(time.RFC3339)}, // No se usa.
				{Key: "display_name", Value: accountDefaults.DISPLAY_NAME},
				{Key: "account_info", Value: accountDefaults.ACCOUNT_INFO},
				{Key: "player_data", Value: DEFAULT_PLAYER_DATA},
				{Key: "player_readonly_data", Value: accountDefaults.PLAYER_READONLY_DATA},
			},
		},
	}

	updateOptions := options.Update()
	updateOptions.SetUpsert(true)

	_, err := accountsCollection.UpdateOne(context.Background(), filter, update, updateOptions)
	if err != nil {
		return nil, err
	}

	result, ok := update[0].Value.(bson.D)
	if !ok {
		panic(0)
	}
	result = append(result, bson.E{Key: "guest_account_id", Value: guestAccountId})

	return result.Map(), nil
}

func mongoReadAccount(query bson.D, projection bson.D) (bson.M, error) {
	options := options.FindOne()
	options.SetProjection(projection)

	var result bson.M

	if err := accountsCollection.FindOne(context.Background(), query, options).Decode(&result); err != nil {
		if err == mongo.ErrNoDocuments {
			return nil, nil
		} else {
			return nil, err
		}
	} else {
		return result, err
	}
}

func mongoUpdateAccount(query bson.D, update bson.D) error {
	updateOptions := options.Update()
	updateOptions.SetUpsert(true)

	_, err := accountsCollection.UpdateOne(context.Background(), query, update, updateOptions)

	return err
}

func mongoGetNewOrderId() int64 {
	var result bson.M
	// Incrementa la entrada <order_id> y devuelve el resultado en result.
	{
		query := bson.D{{Key: "_id", Value: "order_id"}}
		update := bson.D{
			{Key: "$inc",
				Value: bson.D{
					{Key: "sequence_value", Value: int64(1)},
				},
			},
		}
		_, err := sequentialIdCollection.UpdateOne(context.Background(), query, update)
		if err != nil {
			panic(err)
		}

		if err := sequentialIdCollection.FindOne(context.Background(), query).Decode(&result); err != nil {
			panic(err)
		}
	}
	return result["sequence_value"].(int64)
}

func mongoCreateOrder(data bson.D) error {
	_, err := ordersCollection.InsertOne(context.Background(), data)
	return err
}

func mongoUpdateOrder(query bson.D, update bson.D) error {
	_, err := ordersCollection.UpdateOne(context.Background(), query, update)
	return err
}

func mongoReadOrder(query bson.D) (bson.M, error) {
	options := options.FindOne()

	var result bson.M

	if err := ordersCollection.FindOne(context.Background(), query, options).Decode(&result); err != nil {
		if err == mongo.ErrNoDocuments {
			return nil, nil
		} else {
			return nil, err
		}
	} else {
		return result, err
	}
}

// func TestMongodb() {
// 	// database := global_client.Database("gameland")
// 	// accountsCollection := database.Collection("accounts")

// 	// readAccounts(accountsCollection)
// 	// readAccount(accountsCollection, "nn1")
// 	// createAccount(accountsCollection, "abc")
// 	// readAccount(accountsCollection, "abc")
// }
