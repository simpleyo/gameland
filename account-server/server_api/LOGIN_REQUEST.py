from utils import generate_random_str, hashmd5
import datetime

#
# *** DEPRECATED ***
#
# LOGIN_REQUEST  (Paso 1 de LOGIN)
# 1. El cliente envia LOGIN_REQUEST que incluye el account_name.
#    EL servidor comprueba que existe una cuenta con el account_name. Si no existe entonces devuelve login failed.
# 2. El servidor crea una nueva entrada en la lista de request (en caso de que ya
#    exista una request con el mismo account_name se envia el mensaje de login failed al cliente y se elimina esa request),
#    con un tiempo de caducidad asociado a ella. La entrada incluye:
#    el account_name, session_id (generado aleatoriamete), expire_time de la request, y account_one_time_salt.
# 3. El account_one_time_salt lo genera de manera aleatoria el servidor solo para esa
#    peticion concreta.
# 4. El servidor envia session_id, account_one_time_salt y account_salt.
async def LOGIN_REQUEST(req, ws, send_message, database, login_requests_map):

    error_response = {
        "error": "",
        "request_id": req['request_id']
    }

    ### Comprueba si existe una cuenta con el mismo nombre. 

    query = { "account_name": req["account_name"] }
    projection = '_id account_name display_name account_salt account_hash'        
    response = await database.read_account(req, ws, send_message, query, projection)
    if not response: return 

    if not "account_name" in response:
        # No hay una cuenta con ese nombre.
        error_response['error'] = "Account name do not exist."
        await send_message(error_response, ws)  # send error response
        return

    ### Actualiza el estado de login_requests_map

    # Elimina las requests caducadas.
    for k, v in list(login_requests_map.items()): # Hace copia de login_requests_map.items() para poder eliminar elementos mientras se recorre login_requests_map
        if v['expire_time'] <= datetime.datetime.now():
            del login_requests_map[k]

    # Comprueba que no existe una request para el mismo account_name
    for k, v in login_requests_map.items():
        if v['account_name'] == req["account_name"]:
            # Ya existe una request con el mismo account_name se envia el mensaje de login failed al cliente y se elimina esa request.
            del login_requests_map[k]   # Se puede eliminar aqui porque salimos del bucle.
            error_response['error'] = "Login request already exits for this account name."
            await send_message(error_response, ws)  # send error response
            return

    ### Guarda el account_hash y lo elimina de la respuesta que recibira el cliente.

    r = response

    account_hash = r['account_hash']  
    r.pop('account_hash', None)  

    ### Envia la respuesta al cliente

    session_id = hashmd5(generate_random_str(32))
    account_one_time_salt = hashmd5(generate_random_str(32))

    r["request_id"] = req['request_id']
    r["session_id"] = session_id
    r["account_one_time_salt"] = account_one_time_salt

    await send_message(r, ws)  # send response

    ### Procede a crear una nueva request y a insertarla en login_requests_map

    new_request = {
        'account_name': req['account_name'], 
        'session_id': session_id, 
        'account_one_time_salt': account_one_time_salt, 
        'expire_time': datetime.datetime.now() + datetime.timedelta(seconds=5), 
        'account_hash': account_hash,
        'account_id': r['_id']
    }
    login_requests_map[req['request_id']] = new_request 