from utils import generate_random_str
import datetime

# REGISTER_GAMESERVER_INSTANCE:
# 1. El controller (del gameserver node) envia el build_id (identifica la build de la gameserver instance), el lobby_id,
#    la server_ipv4_address, el server_port y los datos necesarios para el matchmaking por parte del accountserver.
# 2. El servidor guarda la informacion y devuelve el lobby_id (Unique identifier generated for the Game Server Instance that is registered. 
#    If LobbyId is specified in request and the game server instance still exists, the LobbyId in request is returned. Otherwise a new lobby id will be returned.)
async def REGISTER_GAMESERVER_INSTANCE(req, ws, send_message, gameservers_info, resource_manager):
   
    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'lobby_id', 'build_id', 'ipv4_address', 'port', 
            'max_player_count', 'server_name', 'game')):
        print("ERROR: REGISTER_GAMESERVER_INSTANCE bad input parameters.")
        return

    game = req['game']
    if not all(k in game for k in ('game_name', 'map_name')):
        print("ERROR: REGISTER_GAMESERVER_INSTANCE bad input parameters.")
        return

    lobby_id = req['lobby_id']
    if not lobby_id in gameservers_info['instances']:
        lobby_id = generate_random_str(32)

        # Elimina los gameserver con el mismo ipv4_address y port.
        ipv4_address = req['ipv4_address']
        port = req['port']    
        gameservers_info['instances'] = { lobby_id: v for lobby_id, v in gameservers_info['instances'].items() if v['ipv4_address'] != ipv4_address or v['port'] != port }

        # Calcula el md5 de los resources.
        # game['resources_md5'] = resource_manager.calculate_resources_md5(game['game_name'], game['resources'])
        # if not isinstance(game['resources_md5'], str):
        #     print("Error al calcular el md5 de los resources del juego <" + game['game_name'] + ">")
        #     game['resources_md5'] = ""

        # Inserta el gameserver.
        gameservers_info['instances'][lobby_id] = {
            'build_id': req['build_id'],
            'ipv4_address': ipv4_address,
            'port': port,
            'expire_time': datetime.datetime.now() + gameservers_info['timeout'],
            ### matchmake info
            'max_player_count': req['max_player_count'], # Numero maximo de jugadores que soporta la gameserver instance
            'server_name': req['server_name'],
            'game': game,

            # tickets es un dict indexado por ticket y sus valores son dict { session_id, expire_time }
            # Contiene los tickets que estan pendientes de validacion.
            #   - ticket        El ticket que se genera cuando el account server recibe el mensaje MATCHMAKE y que
            #                   el player usara para conectarse al game server.
            #   - session_id    Identifica al cliente al que se ha asignado el ticket.
            #   - expire_time   Tiempo en el que el ticket dejara de ser valido y debera ser eliminado de tickets.
            #
            'tickets': {},

            # players es un dict indexado por ticket y sus valores son session_id
            # Contiene los players que estan ocupando un slot en el gameserver.
            #   - ticket        El ticket que se valida cuando el account server recibe el mensaje VALIDATE_MACTHMAKER_TICKET
            #                   por parte del game server, y que este utilizara para identificar al player
            #                   que ocupa uno de sus slots. Cuando se recibe VALIDATE_MACTHMAKER_TICKET, ticket se elimina de tickets
            #                   y se inserta en players.
            #   - session_id    Identifica al player.
            #
            'players': {}
        }

    game_resources = resource_manager.get_game_resources(game['game_name'])

    
    

    # Crea la lista codificada de game resources.
    # A los game resources que debe estar tambien en el client se 
    # les inserta un # al principio de su nombre.
    coded_game_resources = ['#' + k if 'client' in v and v['client'] else k
                            for k, v in game_resources.items()]

    game_maps = resource_manager.get_game_maps(game['game_name'])

    # Crea las listas codificadas con los resources de cada game map.
    # A los game map resources que deben estar tambien en el client se
    # les inserta un # al principio de su nombre.
    coded_game_maps = {map_name: {'resources': ['#' + k if 'client' in v and v['client'] else k
                                                for k, v in map_dict['MAP_RESOURCES'].items()],
                                  'client_resources_md5': resource_manager.calculate_resources_md5(game['game_name'],
                                                [('maps/' + map_name + "/" + k) for k, v in map_dict['MAP_RESOURCES'].items() if 'client' in v and v['client']])}

                       for map_name, map_dict in game_maps.items()}

    response = {
        'request_id': req['request_id'],
        'build_id': req['build_id'],
        'lobby_id': lobby_id,
        'game_resources': coded_game_resources,
        'game_maps': coded_game_maps
    }

    await send_message(response, ws)   # send response