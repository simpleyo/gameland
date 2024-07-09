package server_api

//
// Server API:
//
//   - Implementation commands:
//
//     _internal_GET_RESOURCE
//
//   - Client commands:
//
//     LOGIN_AS_GUEST          // No necesita registrarse. Devuelve un session ticket.
//     LOGIN                   // Hace login en una cuenta existente.
//	   REGISTER_ACCOUNT		   // Registra una nueva cuenta.
//     AUTHENTICATE_SESSION_TICKET          // Validated a client's session ticket, and if successful, returns details for that user
//     UPDATE_PLAYER_DATA
//     MATCHMAKE                            // Attempts to locate a game session matching the given parameters. If the goal is to match the player into a
//                                          // specific active session, only the LobbyId is required. Otherwise, the BuildVersion, GameMode, and Region are
//                                          // all required parameters. Note that parameters specified in the search are required (they are not weighting factors).
//                                          // If a slot is found in a server instance matching the parameters, the slot will be assigned to that player, removing
//                                          // it from the availabe set. In that case, the information on the game session will be returned, otherwise the Status
//                                          // returned will be GameNotFound.
//
//     READ_RANKING             // Obtiene el numero total de elementos en el ranking y los datos del ranking para un numero limitado de entradas.
//     READ_GAME_SERVERS        // Obtiene informacion sobre los game servers.
//
//     GET_GAME_RESOURCE    // Lo utiliza el cliente, despues de recibir la respuesta al comando MATCHMAKE, para recibir los recursos del juego desde el main server.
//                          // Tambien se puede utilizar para obtener los ficheros png de los custom flags.
//
//     BUY_WITH_GOLD    // Lo envia el cliente para solicitar la comprar de algo pagando con oro.
//     PUT_COMMENT
//
//
//   - GameServer commands:
//
//     REGISTER_GAMESERVER_INSTANCE         // Inform the matchmaker that a new Game Server Instance is added.
//     UNREGISTER_GAMESERVER_INSTANCE       // Inform the matchmaker that a Game Server Instance is removed.
//     REFRESH_GAMESERVER_INSTANCE_STATE    // Set the state of the indicated Game Server Instance. Also update the heartbeat for the instance.
//
//     VALIDATE_MACTHMAKER_TICKET           // Validates a Game Server session ticket and returns details about the user
//     NOTIFY_MATCHMAKER_PLAYER_LEFT        // Informs the match-making service that the user specified has left the Game Server Instance. Puede incluir informacion necesaria para actualizar la informacion de la cuenta del usuario que acaba de dejar el gamesever.
//
//     UPDATE_PLAYER_READONLY_DATA          // Para actualizar la experience, por ejemplo.
//     NOTIFY_GAME_TERMINATED               // Se informa al gameserver que el juego ha terminado. Se incluye la informacion necesaria para actualizar la informacion de las cuentas que sea necesario actualizar.
//
//     GET_GAMESERVER_RESOURCE
//
