import math
import pygame
from pygame.math import Vector2
from pygame.locals import *

class StockColor:
    """ ... """
    BLACK = (0, 0, 0)
    RED = (200, 0, 0)
    GREEN = (0, 155, 0)
    BLUE = (0, 0, 155)
    YELLOW = (155, 155, 0)
    ORANGE = (255, 125, 0)
    CYAN = (0, 255, 255)

def catmull_rom_spline_4p(t, p_1, p0, p1, p2):
    """ Catmull-Rom
        (Ps can be numpy vectors or arrays too: colors, curves ...)
    """
        # wikipedia Catmull-Rom -> Cubic_Hermite_spline
        # 0 -> p0,  1 -> p1,  1/2 -> (- p_1 + 9 p0 + 9 p1 - p2) / 16
    # assert 0 <= t <= 1
    return (        
        t*((2-t)*t - 1)   * p_1
        + (t*t*(3*t - 5) + 2) * p0
        + t*((4 - 3*t)*t + 1) * p1
        + (t-1)*t*t         * p2) / 2

def cardinal_spline_4p(t, s, p_1, p0, p1, p2):
    """ Catmull-Rom
        (Ps can be numpy vectors or arrays too: colors, curves ...)
    """
    # wikipedia Catmull-Rom -> Cubic_Hermite_spline
    # 0 -> p0,  1 -> p1,  1/2 -> (- p_1 + 9 p0 + 9 p1 - p2) / 16
    # assert 0 <= t <= 1
    return (
        t*((2-t)*t - 1)   * p_1
        # (2/s-1)t^3 + (-3/s+1)t^2 + (1/s) = t ( t ((2/s-1)t + (-3/s+1) ) + (1/s)
        + (t*(t*((2/s-1)*t + (-3/s+1))) + (1/s)) * p0
        # (-2/s+1)t^3 + (3/s-2)t^2 + t = t ( t ((-2/s+1)t) + 3/s-2 ) + t
        + (t*(t*((-2/s+1)*t + (3/s-2))) + t) * p1
        + (t-1)*t*t         * p2) * s

def draw_closed_spline_points(screen, points, s, col, point_radius):
    P = points
    NP = len(P)
    for i in range(NP):  # skip the ends
        for t in range(10):  # t: 0 .1 .2 .. .9
            a = P[(i+0) % NP]
            b = P[(i+1) % NP]
            c = P[(i+2) % NP]
            d = P[(i+3) % NP]

            p = cardinal_spline_4p(t/10, s, a, b, c, d)

            # draw p
            draw_point(screen, p, col, point_radius)

def draw_spline_points(screen, points, s, col, point_radius):
    P = points
    NP = len(P)
    for i in range(0, NP-3):  # skip the ends
        for t in range(10):  # t: 0 .1 .2 .. .9
            a = P[(i+0) % NP]
            b = P[(i+1) % NP]
            c = P[(i+2) % NP]
            d = P[(i+3) % NP]

            p = cardinal_spline_4p(t/10, s, a, b, c, d)

            # draw p
            draw_point(screen, p, col, point_radius)

def draw_point(screen, p, c, r):
    (x, y) = p
    pygame.draw.circle(screen, c, (int(x+0.5), int(y+0.5)), r)

def draw_line(screen, p1, p2, c):
    pygame.draw.aaline(screen, c, p1, p2, True)

def main():
    # Initialise screen
    pygame.init()
    screen = pygame.display.set_mode((1000, 900))

    pygame.display.set_caption('Test spline')

    radius = 200
    origin = Vector2(500, 450)
    points = [
        origin+(-radius, -radius),
        origin+( radius, -radius),
        origin+( radius,  radius),
        origin+(-radius,  radius)
    ]

    points[0] = origin+(0, -2*radius)
    points[3] = origin+(0,  2*radius)

    # Event loop
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return

        # Fill background
        screen.fill((0, 0, 0))

        # pygame.draw.circle(screen, StockColor.RED, (int(origin.x+0.5), int(origin.y+0.5)), int(math.sqrt(2*(radius*radius)) + 0.5), 1)

        for p in points:
            draw_point(screen, p, StockColor.RED, 5)
        # draw_line(screen, (200, 200), (400, 400), StockColor.GREEN)

        # draw_closed_spline_points(screen, points, 0.84, StockColor.CYAN, 2)
        # draw_closed_spline_points(screen, points, 0.5, StockColor.GREEN, 2)

        draw_spline_points(screen, points, 0.8, StockColor.GREEN, 2)
        # v = points[3] - points[2]
        # v.rotate_ip(1)
        # points[3] = points[2] + v

        pygame.display.update()


if __name__ == '__main__':
    main()
