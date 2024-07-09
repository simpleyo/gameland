from datetime import datetime, timedelta
from utils import hashmd5, date_to_str

# LOGIN
# 1. El cliente calcula key_hash = hash(password + hash(account_name))
# 2. El cliente envia LOGIN(account_name, display_name, key_hash) al servidor.
# 3. El servidor comprueba que existe una cuenta con el account_name. Si no existe entonces la crea.
# 4. El servidor comprueba que account_hash == hashmd5(key_hash + account_salt) y si no es correcto entonces devuelve error.
# 5. El servidor envia al cliente el session_id y los datos del player.
async def LOGIN(req, ws, send_message, accounts_cache):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'account_name', 'create_account', 'key_hash')):
        print("ERROR: LOGIN bad input parameters.")
        return

    error_response = {
        "error": "Invalid ticket.",
        "request_id": req['request_id']
    }  

    valid = False

    ### Comprueba si existe una cuenta con el mismo nombre.

    req["account_name"] = req["account_name"].lower() # Asegura que el nombre de la cuenta esta en minusculas.
    account_name = req["account_name"]

    query = {"account_name": account_name}
    projection = '_id email_validated account_name account_hash account_salt display_name session_id session_expire player_data player_readonly_data'
    response = await accounts_cache.read_account(req, ws, send_message, query, projection)
    if response is None:
        return

    if not response: # if response is empty
        # No hay una cuenta con ese nombre.
        if req["create_account"]:
            response = await accounts_cache.create_account(req, ws, send_message)
            if response is None:
                return
        else:
            error_response["error"] = "Account do not exist."
            await send_message(error_response, ws)
            return
    else:
        if req["create_account"]:
            error_response["error"] = "Account name already exist."
            await send_message(error_response, ws)
            return

        # Actualiza la fecha de caducidad de la session de esta cuenta.
        update = {"session_expire": date_to_str(datetime.now() + timedelta(days=accounts_cache.SESSION_EXPIRE_TIME))}
        response = await accounts_cache.update_account(req, ws, send_message, query, update, projection)
        if response is None:
            return

    ### Comprueba que account_hash = hash(account_salt + key_hash). 

    key_hash     = req['key_hash']
    account_salt = response.pop('account_salt', "")
    account_hash = response.pop('account_hash', "")

    if account_hash == hashmd5(key_hash + account_salt):
        response["request_id"] = req['request_id']
        await send_message(response, ws)  # send response
        valid = True
    else:
        error_response["error"] = "Invalid password."

    ### Envia la error al cliente.

    if not valid:
        await send_message(error_response, ws)

    

    

