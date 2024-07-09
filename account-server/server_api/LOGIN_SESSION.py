import json
import datetime
from utils import generate_random_str, hashmd5


# LOGIN_SESSION  (Paso 2 de LOGIN)
# 1. El cliente debe responder con LOGIN_SESSION antes de que caduque la request. La respuesta debe incluir
#    el login_hash = hash(hash(hash(password) + account_salt) + account_one_time_salt) y el session_id.
# 2. El servidor comprueba que login_hash == hash(account_hash + account_one_time_salt) y si es correcto entonces
#    guarda el session_id en la cuenta y envia los datos del player al cliente.
async def LOGIN_SESSION(req, ws, send_message, database, login_requests_map):

    error_response = {
        "error": "",
        "request_id": req['request_id']
    }

    login_request_id = req['login_request_id']

    if not login_request_id in login_requests_map:
        # No existe una request con el mismo login_request_id se envia el mensaje de login failed al cliente.
        error_response['error'] = "Login request id unknown."
        await send_message(error_response, ws)  # send error response
        return
    else:
        request_info = login_requests_map.pop(login_request_id, None)

    login_hash = req['login_hash']
    account_name = request_info['account_name']
    account_hash = request_info['account_hash']
    account_one_time_salt = request_info['account_one_time_salt']
    account_id = request_info['account_id']

    # Elimina las requests caducadas.
    for k, v in list(login_requests_map.items()): # Hace copia de login_requests_map.items() para poder eliminar elementos mientras se recorre login_requests_map
        if v['expire_time'] <= datetime.datetime.now():
            del login_requests_map[k]
    
    if login_hash == hashmd5(account_hash + account_one_time_salt):
        print("PASS OK")
    else:
        error_response['error'] = "Login has failed."
        await send_message(error_response, ws)  # send error response
        return


    ### Lee datos de la cuenta del cliente

    query = { "account_name": req["account_name"] }
    projection = 'display_name player_data player_readonly_data'
    response = await database.read_account(req, ws, send_message, query, projection)
    if not response: return 

    # r = json.loads("{}")    # response (json)
    r = response

    r["request_id"] = req['request_id']
    r["account_name"] = account_name
    r["session_id"] = req['session_id']
    r["account_id"] = account_id

    await send_message(r, ws)  # send response
