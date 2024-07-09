from datetime import datetime
from utils import str_to_date

# READ_RANKING
# 1. El cliente envia READ_RANKING(session_id) al servidor.
# 2. El servidor comprueba que existe esa session_id y no esta caducada.
# 3. El servidor responde con el ranking.
async def READ_RANKING(req, ws, send_message, accounts_cache, ranking):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'session_id', 'ranking_version')):
        print("ERROR: READ_RANKING bad input parameters.")
        return

    error_response = {
        "error": "Invalid ticket.",
        "request_id": req['request_id']
    }  

    valid = False

    ### Comprueba si existe esa session_id

    session_id = req["session_id"]

    query = {"session_id": session_id}
    projection = 'session_expire guest_account_id account_name'
    response = await accounts_cache.read_account(req, ws, send_message, query, projection)
    if response is None:
        return

    ### Comprueba si la session esta caducada

    if 'session_expire' in response:
        if 'guest_account_id' in response or str_to_date(response['session_expire']) >= datetime.now():

            ranking.update_ranking() # Actualiza ranking

            account_name = response['account_name']
            account_positions = ranking.get_account_positions(account_name)

            del response['session_expire']
            response['session_id'] = session_id
            response["ranking"] = {
                'version': ranking.ranking_version,
                'content': ranking.json_serializable_ranking if ranking.ranking_version != req['ranking_version'] else '',
                'account_positions': account_positions
            }
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

    

    

