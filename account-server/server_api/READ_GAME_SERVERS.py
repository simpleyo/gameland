from datetime import datetime
from utils import str_to_date


# READ_GAME_SERVERS
# 1. El cliente envia READ_GAME_SERVERS(session_id) al servidor.
# 2. El servidor comprueba que existe esa session_id y no esta caducada.
# 3. El servidor responde con informacion sobre los game servers.
async def READ_GAME_SERVERS(req, ws, send_message, accounts_cache, gameservers_info):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'session_id')):
        print("ERROR: READ_GAME_SERVERS bad input parameters.")
        return

    error_response = {
        "error": "Invalid ticket.",
        "request_id": req['request_id']
    }  

    valid = False

    ### Comprueba si existe esa session_id

    session_id = req["session_id"]

    query = {"session_id": session_id}
    projection = 'session_expire guest_account_id'
    response = await accounts_cache.read_account(req, ws, send_message, query, projection)
    if response is None:
        return

    ### Comprueba si la session esta caducada

    if 'session_expire' in response:
        # session_expire_date = datetime_from_json_date_str(response['session_expire'])
        # if session_expire_date >= datetime.datetime.now():
        if 'guest_account_id' in response or str_to_date(response['session_expire']) >= datetime.now():
            del response['session_expire']
            response['session_id'] = session_id
            response["game_servers"] = [{
                'lobby_id': k,
                'server_name': x['server_name'],
                'address': x['ipv4_address'] + ":" + str(x['port']),
                'player_count': len(x['players']),
                'max_player_count': x['max_player_count'],
                'game': x['game']}
                for k, x in gameservers_info['instances'].items()]
            response["request_id"] = req['request_id']

            await send_message(response, ws)  # send response
            valid = True
        else:
            error_response["error"] = "Session is expired."
    else:
        error_response["error"] = "No account found."

    ### Envia error al cliente.

    if not valid:
        await send_message(error_response, ws)

    

    

