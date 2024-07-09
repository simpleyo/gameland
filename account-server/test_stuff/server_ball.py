import sys
from copy import deepcopy
import asyncio
import time
import pygame
from pygame.math import Vector2

class ServerBall:
    DEFAULT_SPEED = 100     # En pixeles / segundo.
    BOOST_MULT = 3

    # Pass the vx, vy as arguments as well.
    def __init__(self, x=200, y=400, vx=0, vy=0):
        self.x = x
        self.y = y
        # Give the objects vx and vy attributes.
        self.vx = vx
        self.vy = vy        
        self.position = (self.x,self.y)
        self.boost = False

    def getPos(self):
        return (self.x, self.y)

    def setPos(self, x, y):
        self.x = x
        self.y = y

    def move(self, dt):
        dx = dt * self.vx
        dy = dt * self.vy
        self.x += dx
        self.y += dy
        # print("Moved ({}, {}) pixels".format(dx, dy))

    # Add a method to update the position and other attributes.
    # Call it every frame.
    def update(self, dt, mouse_pos, boost):
        self.boost = boost
        (mx, my) = mouse_pos
        v = Vector2(mx-self.x, my-self.y)
        if v.length() > 0:
            v = v.normalize()
        if boost:
            v = v * ServerBall.BOOST_MULT * ServerBall.DEFAULT_SPEED
        else:
            v = v * ServerBall.DEFAULT_SPEED
        (self.vx, self.vy) = v

        self.move(dt)
