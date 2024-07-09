from datetime import datetime
from utils import str_to_date

# UPDATE_PLAYER_DATA
# 1. El cliente envia UPDATE_PLAYER_DATA(session_id, player_data) al servidor.
# 2. El servidor comprueba que existe esa session_id y no esta caducada.
# 3. El servidor modifica player_data en la cuenta indicada por session_id.
async def UPDATE_PLAYER_DATA(req, ws, send_message, accounts_cache):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'session_id')):
        print("ERROR: UPDATE_PLAYER_DATA bad input parameters.")
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
            ### Update player_data

            session_id = req["session_id"]

            query = {"session_id": session_id}
            update = {}
            if 'display_name' in req:
                display_name = req['display_name']
                display_name = display_name[:16] # Limita el display name a 16 caracteres unicode.
                update['display_name'] = display_name
            if 'player_data' in req:
                update['player_data'] = req['player_data']
                
            projection = 'session_id session_expire display_name player_data'
            response = await accounts_cache.update_account(req, ws, send_message, query, update, projection)
            if response is None:
                return

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

    

    

