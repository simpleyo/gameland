import json
from .merge_leafs import merge_leafs

# UPDATE_PLAYER_READONLY_DATA:
# Informa al servidor de que un evento de juego ha sucedido en una partida en el gameserver.
# 1. El gameserver envia UPDATE_PLAYER_READONLY_DATA('lobby_id', 'ticket', player_readonly_data) al servidor.
# 2. El servidor comprueba que existe esa session_id y no esta caducada.
# 3. El servidor modifica datos en la cuenta indicada por session_id.
async def UPDATE_PLAYER_READONLY_DATA(req, ws, send_message, accounts_cache, gameservers_info):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'lobby_id', 'ticket', 'player_readonly_data')):
        print("ERROR: UPDATE_PLAYER_READONLY_DATA bad input parameters.")
        return

    error_response = {
        "error": "Invalid ticket.",
        "request_id": req['request_id']
    }    

    lobby_id = req['lobby_id']
    ticket = req['ticket']

    # ATENCION: Lo que llega en req llega como dict de python, es decir, el value de player_readonly_data
    # es un dict no un str.

    valid = False

    session_id = None

    gsinstances = gameservers_info['instances']

    if lobby_id in gsinstances:
        entry = gsinstances[lobby_id]
        players = entry['players']
        
        entry = players.get(ticket, None)

        if entry:
            session_id = entry

            data_dict = {} # El dict que se utilizara para hacer el merge con lo que llega en req['player_readonly_data'].

            query = {"session_id": session_id}
            projection = 'session_id player_readonly_data'
            response = await accounts_cache.read_account(req, ws, send_message, query, projection) # Obtiene player_readonly_data
            if response is None:
                return
            else:
                # Aqui se rellena data_dict con lo que hay en response['player_readonly_data'].
                # ATENCION: Lo que hay en response['player_readonly_data'] es un str no un dict asi que hace falta convertirlo a dict.
                data_dict['player_readonly_data'] = json.loads(response['player_readonly_data'])
                if not 'maps_data' in data_dict['player_readonly_data']:
                    # ATENCION: Las keys que son dict deben ya existir en 'player_readonly_data' antes de poder hacer un merge_leafs
                    data_dict['player_readonly_data']['maps_data'] = {}

            if 'session_id' in response:                

                merge_leafs(data_dict, {'player_readonly_data': req['player_readonly_data']})

                ### Update player_readonly_data

                query = {"session_id": session_id}
                update = {}
                # if 'player_readonly_data' in req:
                #     update['player_readonly_data'] = req['player_readonly_data']
                update['player_readonly_data'] = json.dumps(data_dict['player_readonly_data'])

                projection = 'session_id player_readonly_data'
                response = await accounts_cache.update_account(req, ws, send_message, query, update, projection)
                if response is None:
                    return

                response['lobby_id'] = lobby_id
                response['session_id'] = session_id

                response["request_id"] = req['request_id']
                await send_message(response, ws)  # send response
                valid = True
            else:
                error_response['error'] = "No account found with this session_id."
        else:
            error_response['error'] = "Invalid ticket. Ticket not found in game server list."
    else:
        error_response['error'] = "Game server not found."

    if not valid:
        await send_message(error_response, ws)   # send response

