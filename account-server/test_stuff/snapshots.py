from copy import deepcopy
import pygame
from pygame.math import Vector2

class SnapShots:
    MAX_SIZE = 3

    def __init__(self, value):
        self.data = [deepcopy(value), deepcopy(value), deepcopy(value)]
        self.index = 0
        self.alpha = 0
        self.server_value = deepcopy(value) # para debug

    def s(self):
        return self.data[self.index]
    def c(self):
        return self.data[(self.index+1) % SnapShots.MAX_SIZE]
    def d(self):
        return self.data[(self.index+2) % SnapShots.MAX_SIZE]

    def set_s(self, v):
        self.data[(self.index) % SnapShots.MAX_SIZE] = v
    def set_c(self, v):
        self.data[(self.index+1) % SnapShots.MAX_SIZE] = v
    def set_d(self, v):
        self.data[(self.index+2) % SnapShots.MAX_SIZE] = v

    def _interpolate(self, alpha):  # update c
        s = Vector2(self.s())
        d = Vector2(self.d())
        v = d - s
        c = s + v * alpha
        self.set_c((c.x, c.y))
        self.alpha = alpha

    def update_current(self, alpha):
        self._interpolate(alpha)

    def consume_server_value(self, value, _delta):
        self._advance_with_value(value)
        self.server_value = value
        # print("Alpha: ", self.alpha)
    
    def consume_server_value_v1(self, value, delta):        
        # Hay que calcular un nuevo d() basandose en s() y value, los cuales nos dan una direccion.
        s = Vector2(self.s())
        t = Vector2(value)
        v = (t - s)
        # Valores a ojo viendo la separacion entre c() y server_value en la pantalla.
        # SNAPSHOT_FRAMES = 2 ---> f = 0.1
        # SNAPSHOT_FRAMES = 3 ---> f = 0.25
        # SNAPSHOT_FRAMES = 4 ---> f = 0.35
        # SNAPSHOT_FRAMES = 5 ---> f = 0.45
        f = 0.25
        nd = t + f * v
        self._advance_with_value(nd)
        self.server_value = value


        # # Hay que calcular un nuevo d() basandose en s() y value, los cuales nos dan una direccion.
        # s = Vector2(self.s())
        # nc = Vector2(value)
        # v = (nc - s)
        # # f debe ser >= 0. 
        # # Lo que hace es "estirar" d() (en la direccion de movimiento v) y el resultado es que c() queda mas cerca self.server_value.
        # # Si es 0 entonces no se produce "estiramiento" y c() queda retrasado con respecto a self.server_value.
        # # Si es >0 entonces se produce "estiramiento" y c() queda mas cerca de self.server_value.
        # # A partir de 4 comienza a dar problemas de estabilidad.
        # f = 8
        # nd = nc + v * f * delta

        # self._advance_with_value(nd)
        # self.server_value = value

    def consume_server_value_v3(self, value, delta):
        # Projective Velocity Blending

        # Esto no sirve porque c() y self.server_value quedan muy separados.
        # Sirve para amortiguar los cambios en la posicion, pero lo consigue
        # desligando c() de self.server_value.

        s = Vector2(self.s())
        c = Vector2(self.c())
        d = Vector2(self.d())
        nc = Vector2(value)

        f = 1 # Con f 18, c() y self.server_value quedan mas cerca pero no es estable.
        nd = c + (nc - c) * delta * f

        self._advance_with_value(nd)
        self.server_value = value

    def _advance_with_value(self, snap):
        self.index = ((self.index+1) % SnapShots.MAX_SIZE)
        self.set_c(self.s())  # c() = s()
        self.set_d(deepcopy(snap))  # d() = snap