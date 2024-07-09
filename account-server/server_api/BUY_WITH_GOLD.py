import json
from PIL import Image, UnidentifiedImageError
from datetime import datetime
from utils import str_to_date

# BUY_WITH_GOLD
# 1. El cliente envia BUY_WITH_GOLD(session_id) al servidor.
# 2. El servidor comprueba que existe esa session_id y no esta caducada.
# 3. El servidor responde con el resource o con error.
async def BUY_WITH_GOLD(req, ws, send_message, accounts_cache, game_config):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'session_id', 'game_name', 'item_type', 'item_id')):
        print("ERROR: BUY_WITH_GOLD bad input parameters.")
        return

    error_response = {
        "error": "Invalid ticket.",
        "request_id": req['request_id']
    }

    valid = False

    ### Comprueba si existe esa session_id

    session_id = req["session_id"]

    query = {"session_id": session_id}
    projection = 'guest_account_id session_expire player_readonly_data'
    response = await accounts_cache.read_account(req, ws, send_message, query, projection)
    if response is None:
        return

    ### Comprueba si la session esta caducada

    if 'session_expire' in response:
        # session_expire_date = datetime_from_json_date_str(response['session_expire'])
        # if session_expire_date >= datetime.datetime.now():
        if 'guest_account_id' in response or str_to_date(response['session_expire']) >= datetime.now():

            if req['game_name'] == 'tanks':

                # SKIN

                if req['item_type'] == 'skin':
                    player_readonly_data = response.pop('player_readonly_data', None)
                    assert player_readonly_data is not None
                    max_number_of_skins = game_config['tanks']['MAX_NUMBER_OF_SKINS']
                    item_id = req['item_id']
                    if isinstance(item_id, (int, float)) and not isinstance(item_id, bool):
                        if item_id >= 0 and item_id < max_number_of_skins:                            
                            value = game_config['tanks']['SKIN_PRICES'][item_id]
                            if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
                                player_readonly_data = json.loads(player_readonly_data)
                                skin_ids = player_readonly_data['skin_ids']
                                gold_total = player_readonly_data['gold']
                                if value <= gold_total:
                                    item_id = int(item_id)
                                    if item_id not in skin_ids:
                                        player_readonly_data['gold'] = gold_total - value
                                        skin_ids.append(item_id)

                                        ### Update player_readonly_data

                                        query = {"session_id": session_id}
                                        update = {}
                                        update['player_readonly_data'] = json.dumps(player_readonly_data)

                                        projection = 'session_id player_readonly_data'
                                        response = await accounts_cache.update_account(req, ws, send_message, query, update, projection)
                                        if response is not None:
                                            response["request_id"] = req['request_id']
                                            await send_message(response, ws)  # send response
                                            valid = True
                                        else:
                                            error_response["error"] = "There was a problem updating the account."
                                    else:
                                        error_response["error"] = "You already own that car.\nYou do not need to buy it again."
                                else:
                                    error_response["error"] = "Could not buy.\nYou do not have enough gold."
                            else:
                                error_response["error"] = "Value not valid."
                        else:
                            error_response["error"] = "Item id out of bounds"
                    else:
                        error_response["error"] = "Item id not valid."
                
                # FLAG

                elif req['item_type'] == 'flag':
                    player_readonly_data = response.pop('player_readonly_data', None)
                    assert player_readonly_data is not None
                    max_number_of_flags = game_config['tanks']['MAX_NUMBER_OF_FLAGS']
                    item_id = req['item_id']
                    if isinstance(item_id, (int, float)) and not isinstance(item_id, bool):
                        if item_id >= 0 and item_id < max_number_of_flags:
                            value = game_config['tanks']['FLAG_PRICE']
                            if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
                                player_readonly_data = json.loads(player_readonly_data)
                                flag_ids = player_readonly_data['flag_ids']
                                gold_total = player_readonly_data['gold']
                                if value <= gold_total:
                                    item_id = int(item_id)
                                    if item_id not in flag_ids:
                                        player_readonly_data['gold'] = gold_total - value
                                        flag_ids.append(item_id)

                                        ### Update player_readonly_data

                                        query = {"session_id": session_id}
                                        update = {}
                                        update['player_readonly_data'] = json.dumps(player_readonly_data)

                                        projection = 'session_id player_readonly_data'
                                        response = await accounts_cache.update_account(req, ws, send_message, query, update, projection)
                                        if response is not None:
                                            response["request_id"] = req['request_id']
                                            await send_message(response, ws)  # send response
                                            valid = True
                                        else:
                                            error_response["error"] = "There was a problem updating the account."
                                    else:
                                        error_response["error"] = "You already own that flag.\nYou do not need to buy it again."
                                else:
                                    error_response["error"] = "Could not buy.\nYou do not have enough gold."
                            else:
                                error_response["error"] = "Value not valid."
                        else:
                            error_response["error"] = "Item id out of bounds"
                    else:
                        error_response["error"] = "Item id not valid."
                else:
                    error_response["error"] = "Item type not valid."
            else:
                error_response["error"] = "Game not valid."
        else:
            error_response["error"] = "Session is expired."
    else:
        error_response["error"] = "No account found."

    ### Envia error al cliente.

    if not valid:
        await send_message(error_response, ws)

    

    

