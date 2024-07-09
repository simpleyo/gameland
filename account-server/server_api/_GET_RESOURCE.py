
import datetime
import json
from utils import generate_random_str, hashmd5, datetime_from_json_date_str

# _GET_RESOURCE
# 1. El cliente envia _GET_RESOURCE(session_id) al servidor.
# 2. El servidor comprueba que existe esa session_id y no esta caducada.
# 3. El servidor responde con el resource o con error.
async def _GET_RESOURCE(req, ws, send_message, send_blob, resource_manager):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('game_name', 'resource_path', 'resource_md5')):
        print("ERROR: _GET_RESOURCE bad input parameters.")
        return

    error_response = {
        "error": "Error.",
        "request_id": req['request_id']
    }  

    valid = False

    result = resource_manager.get_resource(req['game_name'], req['resource_path'], req['resource_md5'])

    if not 'error' in result:
        response = {}
        response["request_id"] = req['request_id']

        blob = None

        response["resource_md5"] = result['resource_md5']
        if 'resource_data' in result:
            blob_id = generate_random_str(32)
            response["resource_blob_id"] = blob_id
            blob = 'BLOB'.encode() + blob_id.encode() + result['resource_data']

        await send_message(response, ws)  # send response

        if blob:
            await send_blob(blob, ws)

        valid = True
    else:
        error_response["error"] = result['error']

    ### Envia error al cliente.

    if not valid:
        await send_message(error_response, ws)

    

    

