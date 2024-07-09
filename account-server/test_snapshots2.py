import sys
from copy import deepcopy
import asyncio
import random
import math
import time
import pygame
from pygame.math import Vector2
from test_stuff.snapshots import SnapShots
from test_stuff.client_ball import ClientBall
from test_stuff.server_ball import ServerBall
from test_stuff.server_snake import ServerSnake

#
# Proceso de interpolado de frames en el cliente:
#
#         src                                     dst    
#          | ----- | ----- | ----- | ----- | ----- |
#          0       1       2       3       4       5
#
# La interpolacion va del frame src al frame dst y los frames interpolados estan entre los frames src y dst.
# Los frames src y dst no son frames interpolados. Son los limites del proceso de interpolacion.
# Si interpolated_frames es 4, las posiciones interpoladas se calculan en los frames 1, 2, 3, 4 y, en el frame 5, se alcanza dst_pos.
# Si interpolated_frames es 0, no hay posiciones interpoladas. El frame src_pos es seguido por el frame dst_pos.
#
# El cliente, teoricamente, recibe datos desde el server cada _server->get_max_step_duration() milisegundos.
# El engine recibe, en step(), el _delta, que es el tiempo que ha pasado desde el ultimo step. Teoricamente, _delta
# debe aproximarse a _server->get_max_step_duration(), aunque puede ser diferente en alguna ocasion (siempre sera mayor que cero).
# El cliente produce _client_fps frames segundo. 
# Cuando el cliente recibe datos del server, el frame que sera denotando como src sera el ultimo frame que se pinto.
# Puede darse el caso de que el cliente reciba datos del server antes de llegar a pintar el frame dst.
# El tiempo asignado a un frame comienza en el momento en que termina de pintarse el frame anterior, y termina en el momento
# en que termina de pintarse el frame en cuestion.
# El tiempo total durante el cual el cliente esta interpolando es 
# interpolation_time = (_client_interpolated_frames * get_client_frame_duration()). Es tiempo comienza desde el instante en que
# se termino de pintar el frame src hasta el instante en el que se termine de pintar el frame anterior a dst.
# Si interpolation_time > server_max_step_duration entonces
# el cliente recibira nuevos datos del server antes de que haya comenzado el frame dst. Esto provocara el efecto de que
# el cliente nunca vera todo lo que sucede en el server sino que habra un "time gap" que el cliente no vera.
# Dado el estado A en el tiempo (ta) en el server, el cliente llegara a ver un estado cA que sera el estado
# que tenia A en el tiempo (ta - time_gap)
# El time_gap deberia ser menor que server_max_step_duration ya que de lo contrario sera complicado, por ejemplo, saber el estado
# pasado de un body mas alla de de un tiempo superior a server_max_step_duration.
# Si interpolation_time <= server_max_step_duration entonces
# no habra time gap pero se podran producir parones en la animacion ya que se habra pintado el frame dst y todavia no
# se habran recibido nuevos datos del server para pintar los siguientes frames.
#


pygame.init()
SCREEN = pygame.display.set_mode((1000, 900))

# Devuelve los segundos que han pasado desde la ultima vez que se llamo a esta funcion.
# Usar d['current_ticks'] == 0 para inicializar.
def get_ellapsed_ticks(d): 
    current_ticks = d['current_ticks']
    new_ticks = int(round(time.time() * 1000))
    if current_ticks == 0:
        ellapsed_ticks = 0
    else:
        ellapsed_ticks = new_ticks - current_ticks
    d['current_ticks'] = new_ticks
    return ellapsed_ticks / 1000

server_ball = ServerBall()
client_ball = ClientBall()

server_snake = ServerSnake()

connection_server_side = []    # El servidor pone aqui los paquetes que se deben enviar al cliente.
connection_client_side = []    # El cliente pone aqui los paquetes que se deben enviar al servidor.

client_incoming_packets = []    # Paquetes que llegan al cliente
server_incoming_packets = []    # Paquetes que llegan al servidor

INTERNET_LAG = 0.050 # En segundos.
SERVER_UPS   = 20   # veces por segundo. Cuanto menor sea este valor mas amplio sera el step en el servidor.
CLIENT_FPS   = 60   # veces por segundo.

assert SERVER_UPS <= CLIENT_FPS

# Numero entero positivo que representa el numero de frames entre dos snapshots consecutivos.
# Es el numero maximo que puede tener un indice de frame de snapshot.
# Un snapshot es cada valor que llega desde el servidor.
# SNAPSHOT_FRAMES debe ser mayor que 0y no debe ser menor que math.ceil(CLIENT_FPS / SERVER_UPS)
# El valor ideal es math.ceil(CLIENT_FPS / SERVER_UPS). Dicho valor puede dar problemas de parones
# si los snapshots se retrasan en llegar desde el servidor. Aumentar en 1 SNAPSHOT_FRAMES da margen para
# evitar los parones pero tiene el inconveniente que aleja c() del server_value en los snapshots.
# El valor de SNAPSHOT_FRAMES es un valor que depende fundamentalmente de SERVER_UPS y CLIENT_FPS.
# Cuando mayor es SERVER_UPS menor es SNAPSHOT_FRAMES y, por lo tanto, mas cerca quedara c() del server_value.
SNAPSHOT_FRAMES = math.ceil(CLIENT_FPS / SERVER_UPS)
SNAPSHOT_INTERPOLATED_FRAMES = SNAPSHOT_FRAMES - 1 # Numero de frames interpolados entre snapshots consecutivos.

assert SNAPSHOT_FRAMES > 0
assert SNAPSHOT_FRAMES >= math.ceil(CLIENT_FPS / SERVER_UPS)

SERVER_DELTA = 1 / SERVER_UPS # En segundos.

async def internet_connection_main_loop():
    # Recibe paquetes en connection_server_side y los pone en client_incoming_packets con un retardo de INTERNET_LAG/2
    # Recibe paquetes en connection_client_side y los pone en server_incoming_packets con un retardo de INTERNET_LAG/2

    send_to_client_packets = []
    send_to_server_packets = []

    time_step = 0.001
    time_counter = 0

    while True:
        timeout = time_counter + INTERNET_LAG / 2
    
        # Pone en send_to_server_packets los paquetes que recibe de connection_client_side                
        send_to_server_packets.extend([{'data': x, 'timeout': timeout} for x in connection_client_side])
        connection_client_side.clear()

        # print(send_to_server_packets)

        # Pone en send_to_client_packets los paquetes que recibe de connection_server_side
        # ATENCION: Usando random.randint
        send_to_client_packets.extend([{'data': x, 'timeout': timeout + random.randint(0, 0)/1000} for x in connection_server_side])
        connection_server_side.clear()

        # Envia los paquetes caducados.
        client_incoming_packets.extend([ x['data'] for x in send_to_client_packets if x['timeout'] <= time_counter ])
        server_incoming_packets.extend([ x['data'] for x in send_to_server_packets if x['timeout'] <= time_counter ])

        # Elimina los paquetes caducados.
        send_to_client_packets = [ x for x in send_to_client_packets if x['timeout'] > time_counter ]
        send_to_server_packets = [ x for x in send_to_server_packets if x['timeout'] > time_counter ]

        await asyncio.sleep(time_step)  
        time_counter += time_step

async def server_main_loop():
    await asyncio.sleep(1)  # Da tiempo para que el cliente arranque.

    ticks = {'current_ticks': 0}
    # En segundos
    current_time = get_ellapsed_ticks(ticks)    # Inicializacion.

    delta = 1 / SERVER_UPS
    while True:
        # print("Server time: {}".format(current_time))

        # Aqui se debe actualizar la posicion de la server_ball y enviar la nueva posicion al cliente.
        if server_incoming_packets:
            (mouse_pos, boost) = server_incoming_packets[0] # Asume que solo hay un paquete.
            server_ball.update(delta, mouse_pos, boost)
            server_snake.update(delta, mouse_pos, boost)

            connection_server_side.append((current_time, server_ball.getPos()))

            server_incoming_packets.clear()

        await asyncio.sleep(delta)  
        current_time += get_ellapsed_ticks(ticks)

async def client_main_loop():

    server_start_time = 0   # En segundos. Tiempo del servidor con respecto al que empieza el tiempo del cliente.
    client_time = 0         # En segundos. Tiempo del cliente.
    # server_delta = 0        # En segundos. Diferiencia de tiempo entre el anterior mensaje del servidor y el nuevo que acaba de llegar.

    fps_delay = 1 / CLIENT_FPS # En segundos.

    time_offset = 0     # En segundos. Tiempo acumulado desde que llego el ultimo mensaje del servidor.
    
    mouse_pos = (0, 0)
    boost = False
    
    ticks = {'current_ticks': 0}
    real_time = get_ellapsed_ticks(ticks)    # Inicializacion.

    ellapsed_time = 0 # En segundos.

    snapshots = []

    loop_exit = False
    while not loop_exit:
        for event in pygame.event.get():
            if (event.type == pygame.QUIT or
                event.type == pygame.KEYDOWN and event.key == pygame.K_q):
                loop_exit = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                boost = True
            if event.type == pygame.MOUSEBUTTONUP:
                boost = False
            if event.type == pygame.MOUSEMOTION:
                # event.rel is the relative movement of the mouse.
                mouse_pos = event.pos                  

        # Envia la posicion del raton al servidor
        if not connection_client_side:
            connection_client_side.append((mouse_pos, boost))

        # Recibe la posicion de la ball desde el servidor
        if client_incoming_packets:
            snap = (server_time, server_ball_pos) = client_incoming_packets[0]  # server_time esta en segundos
            # print("Received packet: {}".format((server_time, server_ball_pos)))
            client_incoming_packets.pop(0)
            snapshots.append(snap)

            # server_time es el tiempo (del servidor) en que se envio el paquete que acaba de llegar desde el servidor.

            if server_start_time == 0:
                server_start_time = server_time
                time_offset = 0
                ticks['current_ticks'] = 0
                real_time = get_ellapsed_ticks(ticks)    # Inicializacion.
                print("START")

            # print("Server time: {}".format(server_time))
            # print("Client time: {}".format(client_time))

            new_client_time = (server_time - server_start_time)

            client_time = new_client_time

        if time_offset > SERVER_DELTA or server_start_time == 0:
            if snapshots:
                (server_time, server_ball_pos) = snapshots[0]  # server_time esta en segundos
                snapshots.pop(0)

                client_ball.consume_server_value(server_ball_pos, SERVER_DELTA) #server_delta)

                if time_offset > SERVER_DELTA:
                    time_offset %= SERVER_DELTA
            else:
                time_offset = SERVER_DELTA

        if client_time > 0:
            alpha = time_offset / SERVER_DELTA
            client_ball.update_current_position(alpha)
            # client_ball.update_current_position(time_offset / server_delta)
            # print("Time offset: {0:.3f} Server delta: {1:.3f} Alpha: {2:.3f}".format(time_offset, server_delta, time_offset / server_delta))

        # Clear the SCREEN with fill (or blit a background surface).
        SCREEN.fill((0, 0, 0))
        
        # Draw the ball
        # client_ball.draw_source(SCREEN)    # Dibuja el s() del snapshop
        # client_ball.draw_server(SCREEN)    # Dibuja el d() del snapshop
        client_ball.draw_received_server(SCREEN)    # Dibuja el valor que llego desde el servidor.
        client_ball.draw(SCREEN)                    # Dibuja el c() del snapshop

        # server_snake.draw(SCREEN)

        pygame.display.update()

        await asyncio.sleep(fps_delay)

        ellapsed_time = get_ellapsed_ticks(ticks)

        time_offset += ellapsed_time

        print("Time: {0:.3f} Server Time: {1:.3f} Offset: {2:.3f}".format(real_time - SERVER_DELTA, client_time, ellapsed_time))
        real_time += ellapsed_time
     
    pygame.quit()


asyncio.get_event_loop().create_task(server_main_loop())
asyncio.get_event_loop().create_task(internet_connection_main_loop())

asyncio.get_event_loop().run_until_complete(client_main_loop())

