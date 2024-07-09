import json
import datetime
from utils import generate_random_str, hashmd5, datetime_from_json_date_str
from ._GET_RESOURCE import _GET_RESOURCE

# GET_GAMESERVER_RESOURCE:
# 1. El gameserver envia GET_GAMESERVER_RESOURCE('lobby_id', 'ticket') al servidor.
# 2. El servidor comprueba que existe esa session_id y no esta caducada.
# 3. El servidor responde con el resource o con error.
async def GET_GAMESERVER_RESOURCE(req, ws, send_message, send_blob, gameservers_info, resource_manager):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'lobby_id', 'game_name', 'resource_path', 'resource_md5')):
        print("ERROR: GET_GAMESERVER_RESOURCE bad input parameters.")
        return

    error_response = {
        "error": "Error.",
        "request_id": req['request_id']
    }    

    valid = False

    lobby_id = req['lobby_id']
    gsinstances = gameservers_info['instances']
    if lobby_id in gsinstances:
        entry = gsinstances[lobby_id]

        await _GET_RESOURCE(req, ws, send_message, send_blob, resource_manager)

        valid = True
    else:
        error_response['error'] = "Game server not found."

    if not valid:
        await send_message(error_response, ws)   # send response

