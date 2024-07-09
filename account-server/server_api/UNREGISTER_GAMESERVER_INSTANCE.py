
# UNREGISTER_GAMESERVER_INSTANCE:
# 1. El controller (del gameserver node) envia el lobby_id.
# 2. El servidor elimina la entrada con lobby_id de la lista de gameserver instances.
async def UNREGISTER_GAMESERVER_INSTANCE(req, ws, send_message, gameservers_info):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'lobby_id')):
        print("ERROR: UNREGISTER_GAMESERVER_INSTANCE bad input parameters.")
        return

    lobby_id = req['lobby_id']
    gsinstances = gameservers_info['instances']
    gsinstances.pop(lobby_id, None)

    response = {
        'request_id': req['request_id'],
        'lobby_id': lobby_id
    }

    await send_message(response, ws)   # send response