import datetime
import json
import ssl
import httpx
import requests
import asyncio
import websockets
import server_api
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from resource_server import ResourceManager
from account_ranking import Ranking
# from account_database import Database
from accounts_cache import AccountsCache
from coder import server_code, server_decode
from payments import PayPalManager, Order

XMLRPC_SERVER_URL = 'http://127.0.0.1:8004'
# LOCAL_WS_SERVER_ADDRESS = '0.0.0.0'
# LOCAL_WS_SERVER_PORT = 8002
MAIN_SERVER_PORT = 8002
RESOURCE_SERVER_PATH = '../resource-server'

# database = Database(XMLRPC_SERVER_URL)

accounts_cache = AccountsCache(XMLRPC_SERVER_URL)

resource_manager = ResourceManager(RESOURCE_SERVER_PATH)

paypal_manager = PayPalManager()

login_requests_map = {}
requests_map = {} # Indexado por request_id.
gameservers_info = {
    'instances': {}, # Mapa de gameserver instances. Estan indexadas por lobby_id.
    # Tiempo maximo que puede pasar hasta recibir un REFRESH_GAMESERVER_INSTANCE_STATE.
    # Si se pasa entonces el gameserver instance es eliminado del map.
    'timeout': datetime.timedelta(minutes=1),
    # Tiempo maximo que un ticket puede estar sin validar (ver VALIDATE_MACTHMAKER_TICKET).
    # Si se pasa entonces el ticket se debe eliminar de la lista de tickets.
    'ticket_timeout': datetime.timedelta(seconds=15)
}     

game_config = {
    'tanks': resource_manager.get_game('tanks')
}

ranking = Ranking(accounts_cache, resource_manager.get_game_maps('tanks').keys()) # Inicializa el ranking.

async def send_message(msg, ws):
    request_id = msg['request_id']
    r = requests_map.pop(request_id)
    # await ws.send(server_code(json.dumps(msg), request_id, r['session_key']))
    await ws.send({"type": "websocket.send", "bytes": server_code(json.dumps(msg), request_id, r['session_key'])})
    # print("Sended response to request: " + request_id)

async def send_blob(blob, ws):
    # await ws.send(blob)
    await ws.send({"type": "websocket.send", "bytes": blob})

async def consume_event(data, ws):
    if data is None:
        return

    (cev, session_key) = data
    ev = cev.decode('utf-8')

    print("Consume event: " + ev)

    global login_requests_map
    global requests_map
    global gameservers_info
    global game_config

    # database representa la request que se va a enviar al servidor
    try:
        rq = json.loads(ev)  # event (json)
    except Exception as e:
        print(e)
        return

    if not isinstance(rq, dict):
        return
    
    if not 'request_id' in rq:
        return

    requests_map[rq['request_id']] = {
        'request': rq,
        'session_key': session_key
    }

    if not 'command' in rq:
        return

    command = rq['command']
   
    # Client commands
    if   command == "LOGIN_AS_GUEST":
        await server_api.LOGIN_AS_GUEST(rq, ws, send_message, accounts_cache)
    elif command == "LOGIN":
        await server_api.LOGIN(rq, ws, send_message, accounts_cache)
    elif command == "AUTHENTICATE_SESSION_TICKET":
        await server_api.AUTHENTICATE_SESSION_TICKET(rq, ws, send_message, accounts_cache)
    elif command == "UPDATE_PLAYER_DATA":
        await server_api.UPDATE_PLAYER_DATA(rq, ws, send_message, accounts_cache)
    elif command == "MATCHMAKE":
        await server_api.MATCHMAKE(rq, ws, send_message, accounts_cache, gameservers_info, resource_manager)
    elif command == "READ_RANKING":
        await server_api.READ_RANKING(rq, ws, send_message, accounts_cache, ranking)
    elif command == "READ_GAME_SERVERS":
        await server_api.READ_GAME_SERVERS(rq, ws, send_message, accounts_cache, gameservers_info)
    elif command == "GET_GAME_RESOURCE":
        await server_api.GET_GAME_RESOURCE(rq, ws, send_message, send_blob, accounts_cache, resource_manager)
    elif command == "BUY_WITH_GOLD":
        await server_api.BUY_WITH_GOLD(rq, ws, send_message, accounts_cache, game_config)
    elif command == "PUT_CUSTOM_FLAG":
        await server_api.PUT_CUSTOM_FLAG(rq, ws, send_message, accounts_cache, gameservers_info, resource_manager)

    # Game Server commands
    elif command == "REGISTER_GAMESERVER_INSTANCE":
        await server_api.REGISTER_GAMESERVER_INSTANCE(rq, ws, send_message, gameservers_info, resource_manager)
    elif command == "UNREGISTER_GAMESERVER_INSTANCE":
        await server_api.UNREGISTER_GAMESERVER_INSTANCE(rq, ws, send_message, gameservers_info)
    elif command == "REFRESH_GAMESERVER_INSTANCE_STATE":
        await server_api.REFRESH_GAMESERVER_INSTANCE_STATE(rq, ws, send_message, gameservers_info)
    elif command == "VALIDATE_MACTHMAKER_TICKET":
        await server_api.VALIDATE_MACTHMAKER_TICKET(rq, ws, send_message, accounts_cache, gameservers_info)
    elif command == "NOTIFY_MATCHMAKER_PLAYER_LEFT":
        await server_api.NOTIFY_MATCHMAKER_PLAYER_LEFT(rq, ws, send_message, accounts_cache, gameservers_info)
    elif command == "UPDATE_PLAYER_READONLY_DATA":
        await server_api.UPDATE_PLAYER_READONLY_DATA(rq, ws, send_message, accounts_cache, gameservers_info)
    elif command == "NOTIFY_GAME_TERMINATED":
        await server_api.NOTIFY_GAME_TERMINATED(rq, ws, send_message, accounts_cache, gameservers_info)
    elif command == "GET_GAMESERVER_RESOURCE":
        await server_api.GET_GAMESERVER_RESOURCE(rq, ws, send_message, send_blob, gameservers_info, resource_manager)

async def idle_task():
    while True:

        ### Elimina los tickets caducados.

        gsinstances = gameservers_info['instances']

        for gs in gsinstances.values(): # game server
            tickets = gs['tickets']
            
            # Cuidado: Se eliminan elementos de tickets mientras se recorre. Es necesario hacerlo en dos pasos.
            removed_tickets = []

            for t, v in tickets.items(): # ticket, value
                expire_time = v['expire_time']
                if expire_time < datetime.datetime.now():
                    removed_tickets.append(t)

            for t in removed_tickets:
                tickets.pop(t, None)

            # print('Tickets pendientes de validacion {}'.format(len(tickets))) # para debug

        ### Elimina los game servers que no han recibido REFRESH_GAMESERVER_INSTANCE_STATE.

        # Cuidado: Se eliminan elementos de gsinstances mientras se recorre. Es necesario hacerlo en dos pasos.
        removed_gsinstances = []

        for lb, gs in gsinstances.items(): # game server
            
            expire_time = gs['expire_time']
            if expire_time < datetime.datetime.now():
                removed_gsinstances.append(lb)

        for lb in removed_gsinstances:
            gsinstances.pop(lb, None)

        # Duerme durante un rato.

        await asyncio.sleep(5)        # El loop infinito debe interrumpirse, para volver a continuar despues, en algun momento ya que estamos en una corutina. Esto es lo que se utiliza para que eso pase.

# websockets.serve(...) se encarga de recibir las conexiones de los clientes.
# Para cada una de ellas llama a ws_handler(...) 
async def ws_handler(ws, path):

    # MAX_MESSAGES_PER_CONNECTION = 10    # Numero maximo de mensajes que se permiten recibir en esta conexion.
    MAX_CLIENT_IDLE_TIMEOUT = 180       # En segundos. Tiempo maximo que se permite al cliente estar sin enviar un mensaje.
    # msg_count = 0

    # print("Started connection ---> ", " Remote address: ", ws.remote_address, "Local address: ", ws.local_address)
    print("Started connection ---> ", " Remote address: ", ws.client.host, ":", ws.client.port)

    while True:
        try:
            # msg = await asyncio.wait_for(ws.recv(), timeout=MAX_CLIENT_IDLE_TIMEOUT)
            msg = await asyncio.wait_for(ws.receive(), timeout=MAX_CLIENT_IDLE_TIMEOUT)
        except asyncio.TimeoutError:
            # No data in MAX_CLIENT_IDLE_TIMEOUT seconds, disconnect.
            break
        # except websockets.exceptions.ConnectionClosed as e:
        #     print(e)
        #     break
        else:    
            if msg['type'] == 'websocket.receive':
                if 'text' in msg:
                    msg = msg['text']
                elif 'bytes' in msg:
                    assert type(msg['bytes']) == bytes
                    msg = msg['bytes'].decode('utf-8')

                await consume_event(server_decode(msg), ws)

                # msg_count += 1
                # if msg_count > MAX_MESSAGES_PER_CONNECTION:
                #     break   

            elif msg['type'] == 'websocket.disconnect':
                print('websocket.disconnect received from client')
                break

            # if type(msg) == bytes:
            #     msg = msg.decode('utf-8')
            # await consume_event(server_decode(msg), ws)

            # msg_count += 1
            # # if msg_count > MAX_MESSAGES_PER_CONNECTION:
            # #     break            

    # print("Ended connection ---> ", " Remote address: ", ws.remote_address, "Local address: ", ws.local_address)
    print("Ended connection ---> ", " Remote address: ", ws.client.host, ":", ws.client.port)


######################################################
# Uvicorn is an ASGI web server implementation for Python.
# FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints.
# 
# Uvicorn se encarga del servidor web, con soporte para websockets, en el puerto MAIN_SERVER_PORT.
# FastAPI sirve para construir APIs sobre el web server uvicorn.
#

app = FastAPI() # Poner docs_url=None en el constructor de FastAPI para desactivar la documentacion que se encuentra accesible en <server_address>/docs)

app.add_middleware(GZipMiddleware, minimum_size=1000000, compresslevel=1) # minimum_size - Do not GZip responses that are smaller than this minimum size in bytes. Defaults to 500.

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        await ws_handler(websocket, "")
    except (WebSocketDisconnect, websockets.exceptions.ConnectionClosed) as e:
        print('Cliente {}:{} desconectado. Codigo[{}]'.format(websocket.client.host, websocket.client.port, e))

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/users")
async def users():
    # To return HTTP responses with errors to the client you use HTTPException.
    # raise HTTPException(status_code=404, detail="Item not found")
    return {} # {"users": 100}

@app.post("/api/create-order")
async def create_order(order: Order): # session_id: str = Form(...), value: float = Form(...)
    return paypal_manager.payment_completed(order)
@app.post("/api/payment-canceled-or-error")
async def payment_canceled_or_error(order: Order):
    return paypal_manager.payment_canceled_or_error(order)
@app.post("/api/payment-completed")
async def payment_completed(order: Order):
    return paypal_manager.payment_completed(order)

app.mount("/static", StaticFiles(directory=r"G:\DEV\Projects\gameland\game-client\godot\bin\export\HTML5\Release", html=True), name="static")

# loop='none' evita que uvicorn use su propio loop, lo cual impide que se pueda integrar la task idle_task en el mismo.
# Asi que, en vez de usar, server.run() se usa asyncio.get_event_loop().run_forever() y se pueden insertar las tasks en el loop
# mediante create_task.
config = uvicorn.Config(app=app, host="0.0.0.0", loop='none', port=MAIN_SERVER_PORT, ws="websockets")
                        # ssl_keyfile="./ssl.key",
                        # ssl_certfile="./ssl.crt",
                        # ssl_cert_reqs=ssl.CERT_REQUIRED)


server = uvicorn.Server(config)

asyncio.get_event_loop().create_task(server.serve())
asyncio.get_event_loop().create_task(idle_task())

asyncio.get_event_loop().run_forever()

# server.run() # Probar que funciona con: curl -i http://localhost:8002/users

#
######################################################


# asyncio.get_event_loop().create_task(idle_task())

# LOCAL_WS_SERVER_PORT = MAIN_SERVER_PORT
# asyncio.get_event_loop().run_until_complete(
#     websockets.serve(ws_handler, "0.0.0.0", LOCAL_WS_SERVER_PORT))

# asyncio.get_event_loop().run_forever()
