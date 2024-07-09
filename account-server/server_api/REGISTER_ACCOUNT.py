import json
import server_api.sendmail as sendmail
# import datetime
import xmlrpc.client
from account_defaults import AccountDefaults
from utils import generate_random_str, hashmd5

# REGISTER_ACCOUNT:
# 1. El cliente envia el account_name y un email.
# 2. El servidor duvuelve login failed si existe una cuenta con el mismo nombre. 
# 3. El servidor crea un password y un account_salt aleatorios y guarda este ultimo en la nueva cuenta, 
#    asi como el account_name, el email, y el account_hash = hash(hash(password) + account_salt)
# 4. El servidor envia un email al cliente con el password incluido en el mismo.
# 5. El cliente debera revisar su email para ver el password y utilizarlo en el login.
async def REGISTER_ACCOUNT(req, ws, send_message, accounts_cache):

    error_response = {
        "error": "",
        "request_id": req['request_id']
    }

    ### Comprueba si existe una cuenta con el mismo nombre. 

    try:
        query = { "account_name": req["account_name"] }

        params = { 
            "query": json.dumps(query),
            "projection": 'account_name'        # Indica las propiedades que seran devueltas por readAccount.
        }
        params_str = json.dumps(params)
        response = accounts_cache.readAccount(params_str)
    except xmlrpc.client.Fault as err:
        error_response['error'] = json.dumps(err)
        await send_message(error_response, ws)  # send error response
        return

    if "account_name" in response:
        # Ya hay una cuenta con el mismo nombre
        error_response['error'] = "Account name already exists."
        await send_message(error_response, ws)  # send error response
        return

    ### Procede a crear una nueva cuenta
    
    password = generate_random_str(6)
    account_salt = hashmd5(generate_random_str(32))
    account_hash = hashmd5(hashmd5(password) + account_salt)

    params = {
        "display_name": req["display_name"],
        "account_name": req["account_name"],
        "email": req["email"],
        "account_info": AccountDefaults.ACCOUNT_INFO,
        "player_data": AccountDefaults.PLAYER_DATA,
        "player_readonly_data": AccountDefaults.PLAYER_READONLY_DATA,
        "account_salt": account_salt,
        "account_hash": account_hash,
    }
    params_str = json.dumps(params)
    params["command"] = req['command']

    try:
        response = accounts_cache.createAccount(params_str)
    except xmlrpc.client.Fault as err:
        error_response['error'] = str(err)
        await send_message(error_response, ws)  # send error response
        return

    sendmail.send_email("gameland.noreply@gmail.com", "lolgameland36", "gameland.noreply@gmail.com", 
        "Account registered", "Account name: {}\n Password: {}\n".format(req["account_name"], password))

    print(response)
    r = json.loads(response)    # response (json)

    r["request_id"] = req['request_id']

    await send_message(r, ws)  # send response