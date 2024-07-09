import json
from .merge_leafs import merge_leafs

# NOTIFY_GAME_TERMINATED:
# Informa al servidor de que un evento de juego ha sucedido en una partida en el gameserver.
# 1. El gameserver envia NOTIFY_GAME_TERMINATED('lobby_id', 'ticket', player_readonly_data) al servidor.
# 2. El servidor comprueba que existe esa session_id y no esta caducada.
# 3. El servidor modifica datos en la cuenta indicada por session_id.
async def NOTIFY_GAME_TERMINATED(req, ws, send_message, accounts_cache, gameservers_info):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'lobby_id', 'map_name', 'accounts')):
        print("ERROR: NOTIFY_GAME_TERMINATED bad input parameters.")
        return

    error_response = {
        "error": "",
        "request_id": req['request_id']
    }

    lobby_id = req['lobby_id']

    # ATENCION: Lo que llega en req llega como dict de python, es decir, el value de accounts es un dict no un str.

    valid = True # FIXME Revisar esto.

    gsinstances = gameservers_info['instances']

    if lobby_id in gsinstances:
        _entry = gsinstances[lobby_id]
        
        map_name = req['map_name']
        
        # ranking.handle_notify_game_terminated(req['map_name'], req['accounts'])

        accounts = req['accounts']
        # Para cada cuenta, en <accounts>, actualiza su informacion si es necesario.
        for ac_name, ac_value in accounts.items():
            is_guest_account = ac_value[0]
            query = {"account_name" : ac_name} if not is_guest_account else {"guest_account_id" : ac_name}
            projection = 'account_name player_readonly_data' if not is_guest_account else 'guest_account_id player_readonly_data'

            r = await accounts_cache.read_account(req, ws, send_message, query) # Obtiene player_readonly_data
            if r is None:
                valid = False
                error_response['error'] = "Error reading data."
                continue

            data_dict = {} # El dict que se utilizara para hacer el merge con lo que llega en r['player_readonly_data'].

            # Aqui se rellena data_dict con lo que hay en response['player_readonly_data'].
            # ATENCION: Lo que hay en response['player_readonly_data'] es un str no un dict asi que hace falta convertirlo a dict.
            rod = json.loads(r['player_readonly_data'])
            data_dict['player_readonly_data'] = rod

            if not 'maps_data' in rod: # ATENCION: Las keys que son dict deben ya existir en 'player_readonly_data' antes de poder hacer un merge_leafs                
                rod['maps_data'] = {}
            
            update_list = ac_value[1:] # La entrada debe ser una lista de la forma [score, race_time, best_lap_time]
            update_dict = {'player_readonly_data': {
                'maps_data': {map_name: update_list}}}
            
            # update_dict['player_readonly_data']['experience'] = rod['experience'] + update_list[0] # Incrementa la experience con los puntos que se han ganado.

            if map_name in rod['maps_data']: # Modifica update_dict y update_list segun lo que haya en la cuenta del player.
                # Carga, en entry, los datos que hay actualmente en la cuenta del player.
                entry = rod['maps_data'][map_name] # La entrada debe ser una lista de la forma [score, race_time, best_lap_time]
                update_list[0] += entry[0] # Incrementa la score del map con los puntos que se han ganado.
                if update_list[1] > entry[1]: # Modifica el race_time, en update_list, si es necesario.
                    update_list[1] = entry[1]
                if update_list[2] > entry[2]: # Modifica el best_lap_time, en update_list, si es necesario.
                    update_list[2] = entry[2]

            merge_leafs(data_dict, update_dict)

            ### Update player_readonly_data

            update = {}
            update['player_readonly_data'] = json.dumps(data_dict['player_readonly_data'])
            r = await accounts_cache.update_account(req, ws, send_message, query, update, projection)
            if r is None:
                valid = False
                error_response['error'] = "Error updating data."
                continue

        if valid:
            response = {}
            response["request_id"] = req['request_id']
            await send_message(response, ws)  # send response            
    else:
        error_response['error'] = "Game server not found."

    if not valid:
        await send_message(error_response, ws)   # send response

