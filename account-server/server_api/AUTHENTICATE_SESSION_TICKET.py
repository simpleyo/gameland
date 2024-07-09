import json
from datetime import datetime
from utils import datetime_from_json_date_str, str_to_date

# AUTHENTICATE_SESSION_TICKET:
# 1. Validated a client's session ticket, and if successful, returns details for that user
async def AUTHENTICATE_SESSION_TICKET(req, ws, send_message, accounts_cache):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'session_id')):
        print("ERROR: AUTHENTICATE_SESSION_TICKET bad input parameters.")
        return

    error_response = {
        "error": "",
        "request_id": req['request_id']
    }

    valid = False

    ### Lee datos de la cuenta con session_id
    query = {"session_id": req["session_id"]}
    projection = 'session_id session_expire account_name guest_account_id email_validated display_name player_data player_readonly_data'
    response = await accounts_cache.read_account(req, ws, send_message, query, projection)
    if response is None:
        return

    if "session_id" in response:
        # ATENCION: Hay que comprobar que la session no esta caducada
        if 'guest_account_id' in response or str_to_date(response['session_expire']) >= datetime.now():
            # del response['session_expire']
            response["request_id"] = req['request_id']
            # response["game_config"] = json.dumps(game_config['tanks'])
            await send_message(response, ws)   # send response
            valid = True
        else:
            error_response['error'] = "Session is expired."
    else:
        error_response['error'] = "No account found with this session_id."
        
    if not valid:
        await send_message(error_response, ws)  # send error response

