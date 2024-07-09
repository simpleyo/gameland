import sys
import time
import pygame
from pygame.math import Vector2
from test_stuff.draw import Draw
from test_stuff.colors import StockColor

class Body:    
    COLLISION_COLOR = StockColor.RED

    def __init__(self, x, y, vx, vy, col):
        self.position = Vector2(x, y)
        self.prev_position = Vector2(x, y)
        self.next_position = None
        self.velocity = Vector2(vx, vy)
        self.next_velocity = None
        self.color = col
        self.collided_flag = False # Para debug

    def move(self, delta):
        if self.next_position is not None:
            self.position = self.next_position
            self.next_position = None
        if self.next_velocity is not None:
            self.velocity = self.next_velocity
            self.next_velocity = None

        p = self.position
        v = self.velocity

        self.prev_position = p
        np = p + v * delta
        self.position = np

class CircleBody(Body):
    def __init__(self, x, y, vx, vy, radius, col):
        super().__init__(x, y, vx, vy, col)
        self.radius = radius
        self.static = (vx == 0 and vy == 0)

    def aabb_radius(self):
        return Vector2(self.radius, self.radius)

    def draw(self, col=None):
        p = self.position

        if col is None:
            col = self.color
            if self.collided_flag:
                col = Body.COLLISION_COLOR

        Draw.circle(p, col, self.radius, 1)

        self.collided_flag = False

class RectBody(Body):
    def __init__(self, x, y, vx, vy, rx, ry, col):
        super().__init__(x, y, vx, vy, col)
        self.radius = Vector2(rx, ry)

    def aabb_radius(self):
        return self.radius

    def draw(self, col=None):
        p1 = (p1x, p1y) = (self.position.x - self.radius.x, self.position.y - self.radius.y)
        p2 = (p2x, p2y) = (self.position.x + self.radius.x, self.position.y + self.radius.y)

        if not col:
            col = self.color

        if self.collided_flag:
            col = Body.COLLISION_COLOR

        Draw.line(p1, (p2x, p1y), col)
        Draw.line((p2x, p1y), p2, col)
        Draw.line(p2, (p1x, p2y), col)
        Draw.line((p1x, p2y), p1, col)

        self.collided_flag = False




