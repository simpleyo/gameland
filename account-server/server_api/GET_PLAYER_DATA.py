import datetime
import json
from utils import generate_random_str, hashmd5, datetime_from_json_date_str

#
# *** DEPRECATED ***
#
# GET_PLAYER_DATA
# 1. El cliente envia GET_PLAYER_DATA(session_id) al servidor.
# 2. El servidor comprueba que existe esa session_id y no esta caducada.
# 3. El servidor envia al cliente los datos del player.
async def GET_PLAYER_DATA(req, ws, send_message, database):

    error_response = {
        "error": "Invalid ticket.",
        "request_id": req['request_id']
    }  

    valid = False

    ### Comprueba si existe esa session_id

    session_id = req["session_id"]

    query = { "session_id": session_id }
    projection = 'session_id session_expire player_data'       
    response = await database.read_account(req, ws, send_message, query, projection)
    if not response: return 

    ### Comprueba si la session esta caducada

    session_expire_date = datetime_from_json_date_str(response['session_expire'])
    if session_expire_date >= datetime.datetime.now():
        response["request_id"] = req['request_id']
        await send_message(response, ws)  # send response
        valid = True
    else:
        error_response["error"] = "Session is expired."

    ### Envia error al cliente.

    if not valid:
        await send_message(error_response, ws)

    

    

