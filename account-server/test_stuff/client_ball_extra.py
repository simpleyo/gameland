import sys
from copy import deepcopy
import asyncio
import time
import pygame
from pygame.math import Vector2
from .snapshots_extra import SnapShots

class ClientBall:
    # Pass the vx, vy as arguments as well.
    def __init__(self, x=200, y=400):
        self.snapshots = SnapShots((x, y))
        self.boost = False

    def get_snapshots(self):
        return self.snapshots

    def consume_server_value(self, server_ball_pos, delta, time_offset):
        # Aqui hay que actualizar los snapshots con 
        # la informacion que llega desde el servidor.
        self.snapshots.consume_server_value(server_ball_pos, delta, time_offset)
    
    def update_current_position(self, alpha):
        # Aqui hay que actualizar la posicion actual de la ball.
        self.snapshots.update_current(alpha)

    def draw(self, screen):
        (x, y) = self.snapshots.c()
        if not self.boost:
            pygame.draw.circle(screen, (255,0,0), (int(x), int(y)), 16)
        else:
            pygame.draw.circle(screen, (255,85,0), (int(x), int(y)), 16)

    def draw_source(self, screen):
        (x, y) = self.snapshots.s()
        pygame.draw.circle(screen, (55,55,0), (int(x), int(y)), 16)

    def draw_received_server(self, screen):
        (x, y) = self.snapshots.server_value
        pygame.draw.circle(screen, (0,95,0), (int(x), int(y)), 16)

    def draw_server(self, screen):
        (x, y) = self.snapshots.d()
        pygame.draw.circle(screen, (0,0,155), (int(x), int(y)), 16)


    def draw_s(self, screen):
        (x, y) = self.snapshots.s()
        pygame.draw.circle(screen, (255,0,0), (int(x), int(y)), 4)
    def draw_c(self, screen):
        (x, y) = self.snapshots.c()
        pygame.draw.circle(screen, (0,255,0), (int(x), int(y)), 4)
    def draw_d(self, screen):
        (x, y) = self.snapshots.d()
        pygame.draw.circle(screen, (0,0,255), (int(x), int(y)), 4)

