package server_api

import (
	"account-server/gameservers"
	"account-server/resource_manager"
	"account-server/utils"
	"encoding/json"
	"errors"
	"strings"

	"github.com/gofiber/websocket/v2"
)

type request_REGISTER_GAMESERVER_INSTANCE struct {
	Request_id string
	gameservers.GameServerSpec
	Game map[string]string
}

//REGISTER_GAMESERVER_INSTANCE:
// 1. El controller (del gameserver node) envia el build_id (identifica la build de la gameserver instance), el lobby_id,
//    la server_ipv4_address, el server_port y los datos necesarios para el matchmaking por parte del accountserver.
// 2. El servidor guarda la informacion y devuelve el lobby_id (Unique identifier generated for the Game Server Instance that is registered.
//    If LobbyId is specified in request and the game server instance still exists, the LobbyId in request is returned. Otherwise a new lobby id will be returned.)
func REGISTER_GAMESERVER_INSTANCE(message []byte, sendResponse func([]byte), c *websocket.Conn) error {

	var r request_REGISTER_GAMESERVER_INSTANCE

	// Comprueba que estan todos los parametros requeridos.
	{
		var m map[string]any
		err := json.Unmarshal(message, &m)
		if err != nil {
			return err
		}
		if !utils.ContainsAllKeys(m, []string{"request_id", "lobby_id", "build_id", "address", "port", "region",
			"max_rooms", "max_players_per_room", "server_name", "game"}) {
			err = errors.New("REGISTER_GAMESERVER_INSTANCE bad input parameters")
			return err
		}
	}

	err := json.Unmarshal(message, &r)
	if err != nil {
		return err
	}

	lobbyId := r.Lobby_id

	// gsie := gameservers.GetGameServer(lobbyId)

	if !gameservers.ExistGameServer(lobbyId) {
		remoteAddr := c.Conn.RemoteAddr().String()
		ipv4_address := remoteAddr[:strings.Index(remoteAddr, ":")]

		// Elimina los gameserver con el mismo ipv4_address y port.
		gameservers.RemoveGameServersByAddressAndPort(ipv4_address, r.Port)

		lobbyId = utils.GenerateRandomString(32) //hex.EncodeToString(utils.GenerateRandomBytes(32))

		// Inserta el gameserver.
		gameservers.AddGameServer(&gameservers.GameServerSpec{
			Lobby_id:     lobbyId,
			Build_id:     r.Build_id,
			Ipv4_address: ipv4_address,
			Address:      r.Address,
			Port:         r.Port,
			Region:       r.Region,
			// matchmake info
			Max_rooms:            r.Max_rooms,            // Numero maximo de Room que soporta la gameserver instance
			Max_players_per_room: r.Max_players_per_room, // Numero maximo de jugadores, por Room, que soporta la gameserver instance
			Server_name:          r.Server_name,
			// Game:                 r.Game,
			// RoomPlayerCount:      make([]uint, r.Max_rooms, r.Max_rooms),
		}, r.Game)
	}

	gameResources := resource_manager.GetGameResources(r.Game["game_name"])

	// Crea la lista codificada de game resources.
	// A los game resources que debe estar tambien en el client se
	// les inserta un # al principio de su nombre.
	codedGameResources := []string{}
	for k, v := range gameResources {
		client := false
		if c, ok := v.(map[string]any)["client"]; ok {
			client = c.(bool)
			if client {
				codedGameResources = append(codedGameResources, "#"+k)
			}
		}
		if !client {
			codedGameResources = append(codedGameResources, k)
		}
	}

	gameMaps := resource_manager.GetGameEnabledMaps(r.Game["game_name"])

	// Crea las listas codificadas con los resources de cada game map.
	// A los game map resources que deben estar tambien en el client se
	// les inserta un # al principio de su nombre.
	// ATENCION: Los maps deben guardarse en una lista (no en un map) porque el orden es importante ya que
	// se utilizaran indices en esa lista para realizar la votacion del map.
	codedGameMaps := []dict{}
	for _, iMapName := range gameMaps {
		mapName := iMapName.(string)
		mapDict := resource_manager.GetGame(r.Game["game_name"])["GAME_MAPS"].(dict)[mapName]
		mapResources := mapDict.(map[string]any)["MAP_RESOURCES"].([]any)

		resourcesList := []string{}
		for _, v := range mapResources {
			resource_name := v.([]any)[0].(string)
			client := false
			if c, ok := v.([]any)[1].(map[string]any)["client"]; ok {
				client = c.(bool)
				if client {
					resourcesList = append(resourcesList, "#"+resource_name)
				}
			}
			if !client {
				resourcesList = append(resourcesList, resource_name)
			}
		}

		clientResourcesMd5 := []string{}
		for _, v := range mapResources {
			{
				resource_name := v.([]any)[0].(string)
				client := false
				if c, ok := v.([]any)[1].(map[string]any)["client"]; ok {
					client = c.(bool)
					if client {
						clientResourcesMd5 = append(clientResourcesMd5, "maps/"+mapName+"/"+resource_name)
					}
				}
			}
		}

		var outClientResourcesMd5 string
		outClientResourcesMd5, err = resource_manager.CalculateResourcesMd5(r.Game["game_name"], clientResourcesMd5)
		if err != nil {
			return err
		}

		codedGameMaps = append(codedGameMaps, dict{
			"map_name":             mapName,
			"resources":            resourcesList,
			"client_resources_md5": outClientResourcesMd5,
		})
	}

	response, err := json.Marshal(map[string]any{
		"request_id":      r.Request_id,
		"build_id":        r.Build_id,
		"lobby_id":        lobbyId,
		"game_resources":  codedGameResources,
		"game_maps":       codedGameMaps,
		"game_parameters": resource_manager.GetGameParameters(r.Game["game_name"]),
	})

	if err != nil {
		return err
	}

	sendResponse(response)

	return err
}
