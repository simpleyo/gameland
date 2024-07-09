import json
import datetime

# NOTIFY_MATCHMAKER_PLAYER_LEFT:
# 1. Informs the match-making service that the user specified has left the Game Server Instance
async def NOTIFY_MATCHMAKER_PLAYER_LEFT(req, ws, send_message, accounts_cache, gameservers_info):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'lobby_id', 'ticket')):
        print("ERROR: NOTIFY_MATCHMAKER_PLAYER_LEFT bad input parameters.")
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
        entry = players.pop(ticket, None)
        if entry:
            session_id = entry

            query = { "session_id": session_id }
            projection = 'session_id'
            response = await accounts_cache.read_account(req, ws, send_message, query, projection)
            if response is None:
                return

            if 'session_id' in response:
                response['lobby_id'] = lobby_id
                response['session_id'] = session_id

                response["request_id"] = req['request_id']
                await send_message(response, ws)   # send response

                valid = True
            else:
                error_response['error'] = "No account found with this session_id."
        else:
            error_response['error'] = "Invalid ticket. Ticket not found in game server list."
    else:
        error_response['error'] = "Game server not found."

    if not valid:
        await send_message(error_response, ws)   # send response

    