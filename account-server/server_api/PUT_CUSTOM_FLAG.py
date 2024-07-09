import base64
from PIL import Image, UnidentifiedImageError
import io
from datetime import datetime
from utils import str_to_date

# PUT_CUSTOM_FLAG
# 1. El cliente envia PUT_CUSTOM_FLAG(session_id) al servidor.
# 2. El servidor comprueba que existe esa session_id y no esta caducada.
# 3. El servidor responde con el resource o con error.
async def PUT_CUSTOM_FLAG(req, ws, send_message, accounts_cache, gameservers_info, resource_manager):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'session_id', 'game_name', 'custom_flag_bytes')):
        print("ERROR: PUT_CUSTOM_FLAG bad input parameters.")
        return

    error_response = {
        "error": "Invalid ticket.",
        "request_id": req['request_id']
    }  

    valid = False

    ### Comprueba si existe esa session_id

    session_id = req["session_id"]

    query = { "session_id": session_id }
    projection = 'guest_account_id session_expire account_name player_readonly_data'
    response = await accounts_cache.read_account(req, ws, send_message, query, projection)
    if response is None:
        return

    ### Comprueba si la session esta caducada

    if 'session_expire' in response:
        # session_expire_date = datetime_from_json_date_str(response['session_expire'])
        # if session_expire_date >= datetime.datetime.now():
        if 'guest_account_id' in response or str_to_date(response['session_expire']) >= datetime.now():

            response['session_id'] = session_id
            # response["ranking"] = ranking
            response["request_id"] = req['request_id']

            flag_bytes = base64.b64decode(req["custom_flag_bytes"])

            error_str = ""

            try:
                img = Image.open(io.BytesIO(flag_bytes))
            except UnidentifiedImageError:
                error_str = "# Cannot identify image file."
                img = None

            if img:
                print(img.format, img.size, img.mode)
                if img.format != 'PNG':   
                    error_str += "# Image file must be PNG."
                if img.size != (32, 32):
                    error_str += "\n# Image size must be (32, 32)."
                if img.mode != 'RGBA':
                    error_str += "\n# Image mode must be RGBA."

            if error_str == "":
                img.show()

                del response['session_expire']
                del response['account_name']

                await send_message(response, ws)  # send response

                valid = True

                # cflags_manager = None

                # cflags_md5 = md5(flag_bytes)

                # (cflag_id, cflag_bytes) = cflags_manager.get_by_md5(cflags_md5)
                # if not cflag_bytes:
                #     account_name = response['account_name']
                #     player_readonly_data = response['player_readonly_data']

                #     cflag_id = cflags_manager.add(cflags_md5, cflag_bytes, account_name, player_readonly_data)
                #     assert cflag_id >= cflags_manager.get_first_id()

                #     response['custom_flag_id'] = cflag_id

                #     # await _GET_RESOURCE(req, ws, send_message, send_blob, resource_manager)

                #     del response['session_expire']
                #     del response['account_name']
                #     # del response['player_readonly_data']

                #     await send_message(response, ws)  # send response

                #     valid = True
                # else:
                #     assert cflag_id >= cflags_manager.get_first_id()
                #     error_response["error"] = "Image already exists."
            else:
                error_response["error"] = error_str
        else:
            error_response["error"] = "Session is expired."
    else:
        error_response["error"] = "No account found."

    ### Envia error al cliente.

    if not valid:
        await send_message(error_response, ws)

    

    

