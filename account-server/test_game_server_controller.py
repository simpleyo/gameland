import json
import hashlib
import datetime
import string
import random
import asyncio
import websockets
from coder import client_code, client_decode
from utils import generate_random_str


ACCOUNT_SERVER_ADDRESS = 'localhost'    # Direccion del AccountServer
ACCOUNT_SERVER_PORT = 8002

LOCAL_WS_SERVER_PORT = 8001   # Aqui se debe conectar el GameServer

gameserver_state = {
    'build_id': 'default',
    'ipv4_address': 'localhost',
    'port': 8000,
    'lobby_id': None,
}

gameserver_websocket = None     # websocket con el que el GameServer se conecta al Controller
account_websocket = None     # websocket con el que el Controller se conecta al AccountServer

requests_map = {}    # map indexado por request_id. Contiene todas las request que no han caducado y que todavia no han recibido respuesta.

def new_request_id():
    global requests_map
    rid = random.getrandbits(64)
    while rid in requests_map:
        rid = random.getrandbits(64)
    return rid

async def send_request(query, ws, callback=None, timeout=5, user_data=None):
    global requests_map
    rid = new_request_id()
    query['request_id'] = rid

    requests_map[rid] = { 
        'query': query.copy(),
        'response': None,
        'callback': callback,
        'expire_time': datetime.datetime.now() + datetime.timedelta(seconds=timeout),
        'user_data': user_data
    }

    await ws.send(client_code(json.dumps(query)))
    
async def consume_REGISTER_GAMESERVER_INSTANCE_response(r, q, ws, _user_data):
    if not 'error' in r:
        print("    Lobby id: ", r['lobby_id'])  
        gameserver_state['lobby_id'] = r['lobby_id']
    else:
        print("Recibido error en la respuesta a la request: ", q)
        print("ERROR: ", r['error'])

async def consume_REFRESH_GAMESERVER_INSTANCE_STATE_response(r, q, ws, _user_data):
    if not 'error' in r:
        print("    Lobby id: ", r['lobby_id'])  
    else:
        print("Recibido error en la respuesta a la request: ", q)
        print("ERROR: ", r['error'])

async def consume_response(response_json, ws):    
    response = json.loads(response_json)

    rid = response['request_id']
    
    global requests_map
    if rid in requests_map:
        req = requests_map.pop(rid, None)
        req['response'] = response
        print("Recibida respuesta para: ", req['query']['command'])
    else:
        print("Respuesta recibida desconocida: ", rid)
        return
    
    if req['callback']:
        r = req['response']
        q = req['query']
        await req['callback'](r, q, ws, req['user_data'])

async def consume_local_ws_server_query_response(r, q, _ws, user_data):
    if gameserver_websocket:
        request = { 
            'ws_request_id': user_data,
            'query': q,
            'response': r
        }
        await gameserver_websocket.send(json.dumps(request))        

async def local_ws_server_handler(ws, path):    

    global account_websocket
    global gameserver_websocket
    gameserver_websocket = ws

    RECV_TIMEOUT = 1  # En segundos. Tiempo maximo de espera para recibir el siguiente mensaje.

    while True:
        try:
            query_json = await asyncio.wait_for(ws.recv(), timeout=RECV_TIMEOUT)
        except asyncio.TimeoutError:
            try:
                await asyncio.wait_for(ws.ping(), 5)
            except asyncio.TimeoutError:
                # El GameServer no responde.
                print("El GameServer no responde al PING")
                break
        except websockets.exceptions.ConnectionClosed as e:
            print(e)
            break
        else:   
            assert type(query_json) == str
            query = json.loads(query_json)

            user_data = query.pop('ws_request_id', None)

            print("Enviando ", query['command'], "...")
            await send_request(query, account_websocket, consume_local_ws_server_query_response, 
                        timeout=query['timeout'], user_data=user_data)

    gameserver_websocket = None

async def local_ws_server():    
    await websockets.serve(local_ws_server_handler, 'localhost', LOCAL_WS_SERVER_PORT)

async def remove_expired_requests_task():
    while True:
        if account_websocket:
            global requests_map
            # Elimina las requests caducadas (llamando a los callbacks respectivos antes de eliminarlas).
            callbacks = []
            for k, v in list(requests_map.items()): # Hace copia de requests_map.items() para poder eliminar elementos mientras se recorre requests_map
                if v['expire_time'] <= datetime.datetime.now():
                    req = requests_map[k]
                    if req['callback']:
                        q = req['query']
                        r = {
                            "error": "No response received for request: {}".format(q['request_id']),
                            "request_id": q['request_id']
                        }
                        callbacks.append(req['callback'](r, q, account_websocket, req['user_data']))
                        
                    del requests_map[k]

            if callbacks:
                await asyncio.wait(callbacks, loop=asyncio.get_event_loop())

        await asyncio.sleep(1)

async def main(uri):
    async with websockets.connect(uri) as websocket:
        
        global account_websocket
        
        account_websocket = websocket

        # # REGISTER_GAMESERVER_INSTANCE

        # query = { 
        #     "command": "REGISTER_GAMESERVER_INSTANCE",
        #     "build_id": gameserver_state['build_id'],
        #     'ipv4_address': gameserver_state['ipv4_address'],
        #     'port': gameserver_state['port'],
        #     'lobby_id': ''            
        # }

        # print("Enviando ", query['command'], "...")
        # await send_request(query, websocket, consume_REGISTER_GAMESERVER_INSTANCE_response)

        # response = await websocket.recv()    # Necesita esperar a la respuesta porque el modulo coder no soporta clientes concurrentes, ya que usa session_key y server_session_key de forma global.
        # d_response = client_decode(response).decode('utf-8')
        # await consume_response(d_response, websocket)

        # # REFRESH_GAMESERVER_INSTANCE_STATE

        # query = { 
        #     "command": "REFRESH_GAMESERVER_INSTANCE_STATE",
        #     "lobby_id": gameserver_state['lobby_id'],
        # }

        # print("Enviando ", query['command'], "...")
        # await send_request(query, websocket, consume_REFRESH_GAMESERVER_INSTANCE_STATE_response)

        while True:
            response = await websocket.recv()
            d_response = client_decode(response).decode('utf-8')
            await consume_response(d_response, websocket)

        account_websocket = None

asyncio.get_event_loop().create_task(remove_expired_requests_task())  
asyncio.get_event_loop().create_task(local_ws_server())

try:
    asyncio.get_event_loop().run_until_complete(
        main('ws://' + ACCOUNT_SERVER_ADDRESS + ':' + str(ACCOUNT_SERVER_PORT)))

except (KeyboardInterrupt, websockets.ConnectionClosed) as err:
    print(err)

