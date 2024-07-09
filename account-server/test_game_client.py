import json
import hashlib
import string
import datetime
import random
import asyncio
import websockets
from utils import hashmd5, generate_random_str
from coder import client_code, client_decode

WS_SERVER_ADDRESS = 'localhost'     # Direccion del AccountServer
WS_SERVER_PORT = 8002

client_state = {    # Solo se considera valido si session_id != None
    'session_id': None,         # Si es None entonces hay que hace login de alguna manera.

    'display_name': "Player",
    'is_guest': False,          # Indica si la cuenta utilizada para conectarse al servidor es guest o no.
    'guest_account_id': None,   # Solo se considera valido si is_guest es True.
    'account_name': None,           # Solo se considera valido si is_guest es False.
    'player_data': None,
    'player_readonly_data': None
}

login_tmp = { # Usado solo en el proceso de Login
    'account_name': None,           
    'account_salt': None,           
    'account_one_time_salt': None,
    'session_id': None
}

gui_input = {
    'display_name': "Player",
    'account_name': "test_account",
    'email': "test@gmail.com",
    'password': "1234",
}

client_websocket = None     # websocket con el que el cliente se conecta al AccountServer
requests_map = {}    # map indexado por request_id. Contiene todas las request que no han caducado y que todavia no han recibido respuesta.

def new_request_id():
    global requests_map
    rid = random.getrandbits(64)
    while rid in requests_map:
        rid = random.getrandbits(64)
    return rid

async def send_request(query, ws, callback=None, timeout=5):
    global requests_map
    rid = new_request_id()
    query['request_id'] = rid

    requests_map[rid] = { 
        'query': query.copy(),
        'response': None,
        'callback': callback,
        'expire_time': datetime.datetime.now() + datetime.timedelta(seconds=timeout)
    }

    await ws.send(client_code(rid, json.dumps(query)))

async def consume_LOGIN_AS_GUEST_response(r, q, ws):
    global client_state

    if not 'error' in r:
        print("    Session id: ", r['session_id'])
        print("    Session expire: ", r['session_expire'])
        print("    Guest account id: ", r['guest_account_id'])
        print("    Player data: ", r['player_data'])    
        print("    Player readonly data: ", r['player_readonly_data'])

        client_state['session_id'] = r['session_id']
        client_state['is_guest'] = True
        client_state['display_name'] = r['display_name']
        client_state['player_data'] = r['player_data']
        client_state['player_readonly_data'] = r['player_readonly_data']

       # AUTHENTICATE_SESSION_TICKET

        query = { 
            "command": "AUTHENTICATE_SESSION_TICKET",
            "session_id": client_state['session_id']
        }

        print("Enviando AUTHENTICATE_SESSION_TICKET...")
        await send_request(query, ws, consume_AUTHENTICATE_SESSION_TICKET_response)        

    else:
        print("Recibido error en la respuesta a la request: ", q)
        print("ERROR: ", r['error'])

async def consume_LOGIN_response(r, q, ws):
    global client_state

    if not 'error' in r:
        print("    Session id: ", r['session_id'])
        print("    Session expire: ", r['session_expire'])
        print("    Account name: ", r['account_name'])
        print("    Display name: ", r['display_name'])
        print("    Player data: ", r['player_data'])    
        print("    Player readonly data: ", r['player_readonly_data'])

        client_state['session_id'] = r['session_id']
        client_state['is_guest'] = False
        client_state['account_name'] = r['account_name']
        client_state['display_name'] = r['display_name']
        client_state['player_data'] = r['player_data']
        client_state['player_readonly_data'] = r['player_readonly_data']


        # AUTHENTICATE_SESSION_TICKET

        query = { 
            "command": "AUTHENTICATE_SESSION_TICKET",
            "session_id": client_state['session_id']
        }

        print("Enviando AUTHENTICATE_SESSION_TICKET...")
        await send_request(query, ws, consume_AUTHENTICATE_SESSION_TICKET_response)     

    else:
        print("Recibido error en la respuesta a la request: ", q)
        print("ERROR: ", r['error'])

async def consume_REGISTER_ACCOUNT_response(r, q, ws):
    if not 'error' in r:
        print("    Account name: ", r['account_name'])    
        print("    Account salt: ", r['account_salt'])    
        print("    Account id: ", r['_id'])    
    else:
        print("Recibido error en la respuesta a la request: ", q)
        print("ERROR: ", r['error'])

async def consume_LOGIN_REQUEST_response(r, q, ws):
    if not 'error' in r:
        print("    Session id: ", r['session_id'])    
        print("    Account salt: ", r['account_salt'])    
        print("    Account one time salt: ", r['account_one_time_salt'])    
        print("    Account name: ", r['account_name'])    
        print("    Account id: ", r['_id'])    

        global login_tmp

        login_tmp['session_id'] = r['session_id']
        login_tmp['account_name'] = r['account_name']
        login_tmp['account_salt'] = r['account_salt']
        login_tmp['account_one_time_salt'] = r['account_one_time_salt']        

        # LOGIN_SESSION
        
        if login_tmp['session_id']:
            
            password = gui_input['password']
            account_salt = login_tmp['account_salt']
            account_one_time_salt = login_tmp['account_one_time_salt']
            login_hash = hashmd5(hashmd5(hashmd5(password) + account_salt) + account_one_time_salt)

            query = { 
                "command": "LOGIN_SESSION",
                "request_id": generate_random_str(16),
                "session_id": login_tmp['session_id'],
                "login_hash": login_hash,
                "login_request_id": q['request_id']
            }

            print("Enviando LOGIN_SESSION...")
            await send_request(query, ws, consume_LOGIN_SESSION_response)    
    else:
        print("Recibido error en la respuesta a la request: ", q)
        print("ERROR: ", r['error'])

async def consume_LOGIN_SESSION_response(r, q, ws):
    global client_state

    if not 'error' in r:
        print("    Session id: ", r['session_id'])    
        print("    Account id: ", r['account_id'])    
        print("    Display name: ", r['display_name'])    
        print("    Player data: ", r['player_data'])    
        print("    Player readonly data: ", r['player_readonly_data'])    
        
        client_state['display_name'] = r['display_name']
        client_state['is_guest'] = False
        client_state['session_id'] = r['session_id']
        client_state['player_readonly_data'] = r['player_readonly_data']

        global login_tmp
        login_tmp = {}    
    else:
        print("Recibido error en la respuesta a la request: ", q)
        print("ERROR: ", r['error'])

async def consume_AUTHENTICATE_SESSION_TICKET_response(r, q, ws):
    global client_state

    if not 'error' in r:
        print("    Session id: ", r['session_id'])     
        print("    Session expire: ", r['session_expire'])
        print("    Display name: ", r['display_name'])
        print("    Player data: ", r['player_data'])    
        print("    Player readonly data: ", r['player_readonly_data'])

        client_state['display_name'] = r['display_name']
        client_state['session_id'] = r['session_id']
        client_state['is_guest'] = False
        client_state['guest_account_id'] = None
        client_state['player_readonly_data'] = r['player_readonly_data']

        # GET_PLAYER_DATA

        query = { 
            "command": "GET_PLAYER_DATA",
            "session_id": client_state['session_id']
        }

        print("Enviando GET_PLAYER_DATA...")
        await send_request(query, ws, consume_GET_PLAYER_DATA_response)     

        # UPDATE_PLAYER_DATA

        query = { 
            "command": "UPDATE_PLAYER_DATA",
            "session_id": client_state['session_id'],
            "player_data": "MODIFICADO"
        }

        print("Enviando UPDATE_PLAYER_DATA...")
        await send_request(query, ws, consume_UPDATE_PLAYER_DATA_response)             

    else:
        print("Recibido error en la respuesta a la request: ", q)
        print("ERROR: ", r['error'])
        
async def consume_GET_PLAYER_DATA_response(r, q, ws):
    global client_state

    if not 'error' in r:
        print("    Session id: ", r['session_id'])
        print("    Session expire: ", r['session_expire'])
        print("    Player data: ", r['player_data'])    

        client_state['player_data'] = r['player_data']

    else:
        print("Recibido error en la respuesta a la request: ", q)
        print("ERROR: ", r['error'])

async def consume_UPDATE_PLAYER_DATA_response(r, q, ws):
    global client_state

    if not 'error' in r:
        print("    Session id: ", r['session_id'])
        print("    Session expire: ", r['session_expire'])
        print("    Player data: ", r['player_data'])    

        client_state['player_data'] = r['player_data']

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
        await req['callback'](r, q, ws)

async def remove_expired_requests_task():
    while True:
        if client_websocket:
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
                        callbacks.append(req['callback'](r, q, client_websocket))
                        
                    del requests_map[k]

            if callbacks:
                await asyncio.wait(callbacks, loop=asyncio.get_event_loop())

        await asyncio.sleep(1)

async def main(uri):
    async with websockets.connect(uri) as websocket:

        global client_state
        global gui_input
        global login_tmp
        global client_websocket
                
        client_websocket = websocket

        # LOGIN_AS_GUEST

        # client_state['is_guest'] = True
        # client_state['guest_account_id'] = generate_random_str(32)
        # client_state['session_id'] = None

        # query = { 
        #     "command": "LOGIN_AS_GUEST",
        #     "guest_account_id": client_state['guest_account_id'],
        #     "display_name": client_state['display_name']
        # }

        # print("Enviando LOGIN_AS_GUEST...")
        # await send_request(query, websocket, consume_LOGIN_AS_GUEST_response)

        # LOGIN

        account_name = gui_input['account_name']
        password = gui_input['password']
        key_hash = hashmd5(password + hashmd5(account_name))

        query = { 
            "command": "LOGIN",
            "account_name": gui_input['account_name'],
            "display_name": gui_input['display_name'],
            "key_hash": key_hash
        }

        print("Enviando LOGIN...")
        await send_request(query, websocket, consume_LOGIN_response)

        # REGISTER_ACCOUNT (El proceso de registro hay que cambiarlo. No debe hacer falta recibir emial sel servidor con el password).

        # query = { 
        #     "command": "REGISTER_ACCOUNT",
        #     "display_name": gui_input['display_name'],
        #     "account_name": gui_input['account_name'],
        #     "email": gui_input['email']
        # }

        # print("Enviando REGISTER_ACCOUNT...")
        # await send_request(query, websocket, consume_REGISTER_ACCOUNT_response)

        # LOGIN_REQUEST (Para que esto funcione hay que introducir parametros correctos en gui_input[email, password])

        # login_tmp['account_name'] = gui_input['account_name']
        # login_tmp['account_salt'] = None
        # login_tmp['account_one_time_salt'] = None
        # login_tmp['session_id'] = None

        # query = { 
        #     "command": "LOGIN_REQUEST",
        #     "account_name": login_tmp['account_name'],
        # }

        # print("Enviando LOGIN_REQUEST...")
        # await send_request(query, websocket, consume_LOGIN_REQUEST_response)

        while True:
            response = await websocket.recv()
            d_response = client_decode(response).decode('utf-8')
            await consume_response(d_response, websocket)

        client_websocket = None

asyncio.get_event_loop().create_task(remove_expired_requests_task())  

try:
    asyncio.get_event_loop().run_until_complete(
        main('ws://' + WS_SERVER_ADDRESS + ':' + str(WS_SERVER_PORT)))

except (KeyboardInterrupt, websockets.ConnectionClosed) as err:
    print(err)

