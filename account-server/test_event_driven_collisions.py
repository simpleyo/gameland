import math
from copy import deepcopy
import heapq
import pygame
from pygame.time import Clock
from pygame.math import Vector2
from pygame.locals import *
from test_stuff.collision_body import RectBody, CircleBody
from test_stuff.colors import StockColor
from test_stuff.draw import Draw

class CollisionType:
    CIRCLE_VS_WORLD_LIMIT = 0
    CIRCLE_VS_CIRCLE = 1

class Collision:
    def __init__(self, t, ct, data):
        self.t = t
        self.ct = ct
        self.data = data

    def __lt__(self, other):
        return self.t < other.t

class Simulation:
    """ La deteccion de colisiones entre bodies se realiza a priori, es decir,
    se detectan antes de mover los bodies. Para la deteccion se utilizan
    las posiciones actuales y las velocidades de los bodies.

    El metodo solve_collisions(delta, world_bodies) se encarga de detectar las colisiones
    que se producen en el intervalo de tiempo [time, time+delta], siendo time el tiempo en
    que el body comienza la iteracion y time+delta el tiempo en el que termina esta la
    misma.

    Usar heapq para la priority queue.

     """

    def __init__(self, world_origin, world_radius):
        self.world_origin = world_origin
        self.world_radius = world_radius
        origin = world_origin
        radius = world_radius
        self.world_wall_bodies = [
            RectBody(origin.x-radius*2, origin.y, 0, 0, radius, radius, StockColor.GREEN),
            RectBody(origin.x+radius*2, origin.y, 0, 0, radius, radius, StockColor.GREEN),
            RectBody(origin.x, origin.y-radius*2, 0, 0, radius, radius, StockColor.GREEN),
            RectBody(origin.x, origin.y+radius*2, 0, 0, radius, radius, StockColor.GREEN)
        ]        

        self.delta = 0
        self.collisions = []
        self.count = 0 # for debug
        self.debug_bodies = []  # Cada entrada es [frames, color, body, position]

    def solve_collisions(self, delta, world_bodies):
        """ Detecta colisiones entre cada unos de los world_bodies y los world_wall_bodies y
        entre cada uno de los world_bodies y el resto de world_bodies. """

        self.delta = delta

        self.collisions.clear()

        # Detecta las colisiones.

        self._solve_world_limits(world_bodies)

        for i, a in enumerate(world_bodies):
            for b in world_bodies[i+1:]:
                r = self._collide(a, b)
                if r:
                    self.collisions.append(r)

        # Ordena las colisiones por tiempo.

        self.collisions.sort(key=lambda x: x[0])

        # Resuelve las colisiones.

        show_info = False
        first = False

        for c in self.collisions:
            if not first:
                first = True
                # print("Begin")
                
            assert c
            (t, ct, data) = c
            # assert t >= 0
            if ct == CollisionType.AABB_VS_WORLD_LIMIT:
                (b, (dx, dy)) = data
                b.next_position = Vector2(b.position)
                b.next_position += (dx, dy)
                if dx != 0:
                    b.next_velocity = Vector2(b.velocity)
                    b.next_velocity.x = -b.velocity.x
                if dy != 0:
                    b.next_velocity = Vector2(b.velocity)
                    b.next_velocity.y = -b.velocity.y

                # Dibuja el body en el momento de la colision.
                # dp = b.prev_position + b.velocity * t
                # self.debug_bodies.append([20, StockColor.GREEN, deepcopy(b), dp])

                b.collided_flag = True

            elif ct == CollisionType.AABB_VS_AABB or \
                 ct == CollisionType.CIRCLE_VS_CIRCLE:
                (a, b) = data

                # Dibuja los body en el momento de la colision.
                # dp = a.prev_position + a.velocity * t
                # self.debug_bodies.append([1, StockColor.GREEN, deepcopy(a), dp])
                # dp = b.prev_position + b.velocity * t
                # self.debug_bodies.append([1, StockColor.GREEN, deepcopy(b), dp])

                # Marca los bodies como colisionados.
                a.collided_flag = True
                b.collided_flag = True

            self.count += 1
            if show_info:
                cts = "AABB_VS_WORLD_LIMIT" if ct == CollisionType.AABB_VS_WORLD_LIMIT else \
                    "AABB_VS_AABB" if ct == CollisionType.AABB_VS_AABB else \
                    "CIRCLE_VS_CIRCLE" if ct == CollisionType.CIRCLE_VS_CIRCLE else ""
                print("Collision: {} Type: {} Time: {}".format(self.count, cts, t))

    def draw_world_limits(self):
        for body in self.world_wall_bodies:
            body.draw()

    def draw_debug_bodies(self):
        debug_bodies = []
        for d in self.debug_bodies:
            (frames, col, b, position) = d
            d[0] -= 1
            if frames >= 0:
                pb = b.position
                b.position = position
                b.draw(col)
                b.position = pb
                debug_bodies.append(d)

        self.debug_bodies = debug_bodies

def main():
    # Initialise screen
    pygame.init()
    screen_size = (1000, 900)
    screen = pygame.display.set_mode(screen_size)
    clock = Clock()
    FPS = 60
    delta = 1 / FPS

    pygame.display.set_caption('Test event driven collisions')

    origin = Vector2(screen_size[0] / 2, screen_size[1]/ 2)
    world_radius = 400

    world_bodies = [
        # CircleBody(origin.x, origin.y, 3000, 120, 64, StockColor.CYAN),
        CircleBody(origin.x, origin.y, 110, 120, 128, StockColor.CYAN),
        CircleBody(origin.x, origin.y, 140, 500, 128, StockColor.CYAN),
        # CircleBody(origin.x, origin.y, 140, 300, 64, StockColor.CYAN),
        # CircleBody(origin.x, origin.y, 200, 250, 64, StockColor.CYAN),
        # RectBody(origin.x, origin.y, 4400, 400, 32, 32, StockColor.CYAN),
        # RectBody(origin.x, origin.y, -400, 300, 32, 132, StockColor.CYAN),
        # RectBody(origin.x, origin.y, 430, 700,  32, 132, StockColor.CYAN),
        # RectBody(origin.x, origin.y, 500, 100,  32, 32, StockColor.CYAN),
        # RectBody(origin.x, origin.y, 200, 200,  32, 32, StockColor.CYAN),
        # RectBody(origin.x, origin.y, 50, 100,  128, 32, StockColor.CYAN),
        # RectBody(origin.x, origin.y, 100, 70,  128, 32, StockColor.CYAN),
    ]

    simulation = Simulation(origin, world_radius)

    # Event loop
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return

        # Fill background
        screen.fill((0, 0, 0))

        for body in world_bodies:
            body.move(delta)

        simulation.solve_collisions(delta, world_bodies)

        simulation.draw_world_limits()
        simulation.draw_debug_bodies()
        for body in world_bodies:
            body.draw()

        pygame.display.update()

        clock.tick(FPS)


if __name__ == '__main__':
    main()
