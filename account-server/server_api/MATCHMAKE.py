import json
import datetime
from utils import generate_random_str

# MATCHMAKE:
# 1. Busca un slot disponible en un gameserver y devuelve el ticket al cliente.
async def MATCHMAKE(req, ws, send_message, accounts_cache, gameservers_info, resource_manager):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'session_id', 'game_name', 'game_client_resources_md5')):
        print("ERROR: MATCHMAKE bad input parameters.")
        return

    error_response = {
        "error": "Invalid ticket.",
        "request_id": req['request_id']
    }    

    session_id = req['session_id']

    ### Comprueba que exite el session_id
    query = {"session_id": session_id}
    projection = 'session_id'
    response = await accounts_cache.read_account(req, ws, send_message, query, projection)
    if response is None:
        return

    valid = False

    if 'session_id' in response:
    
        gsinstances = gameservers_info['instances']

        ### Comprueba que no exista ya un ticket para ese session_id
        ticket = None
        exit_loop = False
        for lobby_id, gs in gsinstances.items():
            if exit_loop:
                break
            for tk, tk_data in gs['tickets'].items():
                if tk_data['session_id'] == session_id:
                    ticket = tk
                    exit_loop = True
                    break

            for tk, ss_id in gs['players'].items():
                if ss_id == session_id:
                    ticket = tk
                    exit_loop = True
                    break
        
        ### Si no existe ya un ticket entonces crea uno nuevo.
        if not ticket:
            # Busca los game servers que tienen algun slot libre y que estan sirviendo
            # el juego 'game_name'.
            gss = [(lobby_id, gs) for lobby_id, gs in gsinstances.items() 
                if len(gs['players']) < gs['max_player_count'] and
                gs['game']['game_name'] == req['game_name']]

            if gss:
                # Elige el primero de la lista
                selected_index = 0
                lobby_id = gss[selected_index][0]
                gs = gss[selected_index][1]

                tickets = gs['tickets']

                ticket = generate_random_str(32)
                tickets[ticket] = {
                    'session_id': session_id,
                    'expire_time': datetime.datetime.now() + gameservers_info['ticket_timeout']
                }
                print('Tickets asignados {}/{}'.format(len(gs['players']), gs['max_player_count']))
                print('Tickets pendientes de validacion {}'.format(len(tickets)))

        ### Si hay ticket entonces lo envia al cliente.
        if ticket:
            response['ticket'] = ticket

            game_client_resources_md5 = resource_manager.get_game_client_resources_md5(req['game_name'])
            
            # game_resources_md5 = gs['game']['resources_md5']

            gameserver_info = {
                'lobby_id': lobby_id,
                'build_id': gs['build_id'],
                'ipv4_address': gs['ipv4_address'],
                'port': gs['port'],
                'player_count': len(gs['players']),
                'max_player_count': gs['max_player_count'],
                'game_name': gs['game']['game_name'],
                'game_client_resources_md5': game_client_resources_md5,
                'game_map_names': [x for x in resource_manager.get_game_maps(req['game_name']).keys()] # Nombres de todos los mapas del juego
            }

            if game_client_resources_md5 != req['game_client_resources_md5']:
                gameserver_info['game_client_resources'] = resource_manager.get_game_client_resources(req['game_name'])

            response['gameserver_info'] = gameserver_info

            response["request_id"] = req['request_id']
            await send_message(response, ws)   # send response

            valid = True
        else:
            error_response['error'] = "All game servers are busy."
    else:
        error_response['error'] = "No account found with this session_id."

    if not valid:
        await send_message(error_response, ws)   # send response

    