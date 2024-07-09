import json
import datetime

# REFRESH_GAMESERVER_INSTANCE_STATE:
# 1. El controller (del gameserver node) envia el lobby_id.
# 2. El servidor actualiza el estado de la instancia en la lista de gameserver instances.
#    Si no existe el lobby_id en la lista de los game servers entonces devuelve lobby_id vacio.
async def REFRESH_GAMESERVER_INSTANCE_STATE(req, ws, send_message, gameservers_info):

    # Aqui se debe comprobar que la req es correcta y en caso contrario se ignora sin enviar nada al cliente.
    if not all(k in req for k in ('request_id', 'lobby_id')):
        print("ERROR: REFRESH_GAMESERVER_INSTANCE_STATE bad input parameters.")
        return

    lobby_id = req['lobby_id']
    gsinstances = gameservers_info['instances']
    if lobby_id in gsinstances:
        entry = gsinstances[lobby_id]
        expire_time = entry['expire_time']
        if expire_time >= datetime.datetime.now():
            entry['expire_time'] = datetime.datetime.now() + gameservers_info['timeout']
        else:
            gameservers_info.pop(lobby_id, None)
    else:
        lobby_id = ""
    
    response = {
        'request_id': req['request_id'],
        'lobby_id': lobby_id
    }

    await send_message(response, ws)   # send response