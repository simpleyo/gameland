import json
import datetime

# VALIDATE_MACTHMAKER_TICKET:
# 1. Validates a Game Server session ticket and returns details about the user
async def VALIDATE_MACTHMAKER_TICKET(req, ws, send_message, accounts_cache, gameservers_info):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'lobby_id', 'ticket')):
        print("ERROR: VALIDATE_MACTHMAKER_TICKET bad input parameters.")
        return

    error_response = {
        "error": "Invalid ticket.",
        "request_id": req['request_id']
    }  

    lobby_id = req['lobby_id']
    ticket = req['ticket']

    valid = False

    gsinstances = gameservers_info['instances']

    if lobby_id in gsinstances:
        entry = gsinstances[lobby_id]
        players = entry['players']
        tickets = entry['tickets']
        if ticket in tickets:
            session_id = tickets[ticket]['session_id']

            tickets.pop(ticket, None)

            # Comprueba que existe una cuenta con el session_id dado
            query = { "session_id": session_id }
            projection = 'account_name guest_account_id display_name player_data player_readonly_data'
            response = await accounts_cache.read_account(req, ws, send_message, query, projection)
            if response is None:
                return

            if response: # if response is not empty
                if len(players) < entry['max_player_count']:
                    players[ticket] = session_id

                    response['lobby_id'] = lobby_id
                    response['session_id'] = session_id

                    response["request_id"] = req['request_id']
                    await send_message(response, ws)   # send response

                    valid = True
                else:
                    error_response["error"] = "Game server is full."
            else:
                error_response["error"] = "No account found."
        else:
            error_response["error"] = "Ticket not found."
    else:
        error_response["error"] = "Game server not found."

    if not valid:
        await send_message(error_response, ws)   # send response

    