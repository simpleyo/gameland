#
#  Server API:
#     
#    - Implementation commands:
#     
#      _GET_RESOURCE
#
#    - Client commands:
#
#      LOGIN_AS_GUEST          // No necesita registrarse. Devuelve un session ticket.
#      LOGIN                   // Hace login en una cuenta existente o crea una nueva.
#      AUTHENTICATE_SESSION_TICKET          // Validated a client's session ticket, and if successful, returns details for that user 
#      UPDATE_PLAYER_DATA
#      MATCHMAKE                            // Attempts to locate a game session matching the given parameters. If the goal is to match the player into a 
#                                           // specific active session, only the LobbyId is required. Otherwise, the BuildVersion, GameMode, and Region are 
#                                           // all required parameters. Note that parameters specified in the search are required (they are not weighting factors). 
#                                           // If a slot is found in a server instance matching the parameters, the slot will be assigned to that player, removing 
#                                           // it from the availabe set. In that case, the information on the game session will be returned, otherwise the Status
#                                           // returned will be GameNotFound.
#      REQUEST_ACCOUNT_UPGRADE_CODE
#      UPGRADE_ACCOUNT
#      REQUEST_ACCOUNT_RECOVERY_DATA
#      READ_RANKING             // Obtiene el numero total de elementos en el ranking y los datos del ranking para un numero limitado de entradas.
#      READ_GAME_SERVERS        // Obtiene informacion sobre los game servers.
#
#      GET_GAME_RESOURCE    // Lo utiliza el cliente, despues de recibir la respuesta al comando MATCHMAKE, para recibir los recursos del juego desde el main server.
#                           // Tambien se puede utilizar para obtener los ficheros png de los custom flags.        
#
#      BUY_WITH_GOLD    // Lo envia el cliente para solicitar la comprar de algo pagando con oro.
#
#      (deprecated) REGISTER_ACCOUNT
#      (deprecated) LOGIN_REQUEST     # Paso 1 de LOGIN  
#      (deprecated) LOGIN_SESSION     # Paso 2 de LOGIN  // Devuelve un session ticket.
#   
#      (deprecated) GET_PLAYER_DATA                      // Por ejemplo, display_name, skin_id, color_id.
#      (deprecated) GET_PLAYER_READ_ONLY_DATA            // Son los datos que solo debe poder modificar el servidor. (Por ejemplo, experience)
#      (deprecated) SEND_ACCOUNT_RECOVERY_EMAIL
#
#
#    - GameServer commands:
# 
#      REGISTER_GAMESERVER_INSTANCE         // Inform the matchmaker that a new Game Server Instance is added.
#      UNREGISTER_GAMESERVER_INSTANCE       // Inform the matchmaker that a Game Server Instance is removed.
#      REFRESH_GAMESERVER_INSTANCE_STATE    // Set the state of the indicated Game Server Instance. Also update the heartbeat for the instance.
#
#      VALIDATE_MACTHMAKER_TICKET           // Validates a Game Server session ticket and returns details about the user
#      NOTIFY_MATCHMAKER_PLAYER_LEFT        // Informs the match-making service that the user specified has left the Game Server Instance
#
#      UPDATE_PLAYER_READONLY_DATA          // Para actualizar la experience, por ejemplo.
#      NOTIFY_GAME_TERMINATED               // Se informa al gameserver que el juego ha terminado. Se incluye la informacion necesaria para actualizar la informacion de las cuentas que sea necesario actualizar.
#
#      GET_GAMESERVER_RESOURCE
#

from .LOGIN_AS_GUEST import LOGIN_AS_GUEST
from .REGISTER_ACCOUNT import REGISTER_ACCOUNT
from .LOGIN import LOGIN
from .LOGIN_REQUEST import LOGIN_REQUEST
from .LOGIN_SESSION import LOGIN_SESSION
from .AUTHENTICATE_SESSION_TICKET import AUTHENTICATE_SESSION_TICKET
from .GET_PLAYER_DATA import GET_PLAYER_DATA
from .UPDATE_PLAYER_DATA import UPDATE_PLAYER_DATA
from .MATCHMAKE import MATCHMAKE
from .REQUEST_ACCOUNT_UPGRADE_CODE import REQUEST_ACCOUNT_UPGRADE_CODE
from .UPGRADE_ACCOUNT import UPGRADE_ACCOUNT
from .REQUEST_ACCOUNT_RECOVERY_DATA import REQUEST_ACCOUNT_RECOVERY_DATA
from .READ_RANKING import READ_RANKING
from .READ_GAME_SERVERS import READ_GAME_SERVERS
from .GET_GAME_RESOURCE import GET_GAME_RESOURCE
from .BUY_WITH_GOLD import BUY_WITH_GOLD

from .REGISTER_GAMESERVER_INSTANCE import REGISTER_GAMESERVER_INSTANCE
from .UNREGISTER_GAMESERVER_INSTANCE import UNREGISTER_GAMESERVER_INSTANCE
from .REFRESH_GAMESERVER_INSTANCE_STATE import REFRESH_GAMESERVER_INSTANCE_STATE
from .VALIDATE_MACTHMAKER_TICKET import VALIDATE_MACTHMAKER_TICKET
from .NOTIFY_MATCHMAKER_PLAYER_LEFT import NOTIFY_MATCHMAKER_PLAYER_LEFT
from .UPDATE_PLAYER_READONLY_DATA import UPDATE_PLAYER_READONLY_DATA
from .NOTIFY_GAME_TERMINATED import NOTIFY_GAME_TERMINATED
from .GET_GAMESERVER_RESOURCE import GET_GAMESERVER_RESOURCE
from .PUT_CUSTOM_FLAG import PUT_CUSTOM_FLAG



