from copy import deepcopy
import pygame
from pygame.math import Vector2

class SnapShots:
    MAX_SIZE = 2

    def __init__(self, value):
        self.data = [deepcopy(value), deepcopy(value)]
        self.index = 0
        self.alpha = 0
        self.current_value = deepcopy(value)
        self.server_value = deepcopy(value) # Para debug

    def s(self):
        return self.data[self.index]
    def d(self):
        return self.data[(self.index+1) % SnapShots.MAX_SIZE]
    def c(self):
        return self.current_value

    def set_s(self, v):
        self.data[(self.index)] = v
    def set_d(self, v):
        self.data[(self.index+1) % SnapShots.MAX_SIZE] = v
    def set_c(self, v):
        self.current_value = v

    def _extrapolate(self, alpha):  # update c
        s = Vector2(self.s())
        d = Vector2(self.d())
        c = Vector2(self.c())
        v = d - s
        c = (d + v * alpha)
        self.set_c((c.x, c.y))
        self.alpha = alpha

    def update_current(self, alpha):
        self._extrapolate(alpha)

    def consume_server_value(self, value, _delta, time_offset):
        self.server_value = value
        s = Vector2(self.s())
        d = Vector2(self.d())
        v = d - s

        v2 = value - d
        f = 0.5
        v3 = (v2 * f) + (v * (1-f))

        nd = d + v3
        # nd = value

        self._advance_with_value(nd)
    
    def _advance_with_value(self, snap):
        self.index = ((self.index+1) % SnapShots.MAX_SIZE)
        self.set_d(deepcopy(snap))  # d() = snap


