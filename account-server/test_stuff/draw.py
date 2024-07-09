import pygame
from pygame.math import Vector2
from pygame.locals import *

class Draw:
    @staticmethod
    def circle(p, c, r, w=0):
        screen = pygame.display.get_surface()
        (x, y) = p
        pygame.draw.circle(screen, c, (int(x+0.5), int(y+0.5)), r, w)

    @staticmethod
    def line(p1, p2, c):
        screen = pygame.display.get_surface()
        pygame.draw.aaline(screen, c, p1, p2, True)

    @staticmethod
    def lines(point_list, c):
        screen = pygame.display.get_surface()
        pygame.draw.lines(screen, c, True, point_list)

    @staticmethod
    def rect(p1, p2, c):
        screen = pygame.display.get_surface()
        (p1x, p1y) = p1
        (p2x, p2y) = p2
        pygame.draw.line(screen, c, p1, (p2x, p1y))
        pygame.draw.line(screen, c, (p2x, p1y), p2)
        pygame.draw.line(screen, c, p2, (p1x, p2y))
        pygame.draw.line(screen, c, (p1x, p2y), p1)
