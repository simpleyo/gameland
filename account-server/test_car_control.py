import os
import math
# import box2d
from copy import deepcopy
import pygame
from pygame.time import Clock
from pygame.math import Vector2
from pygame.locals import *
from test_stuff.car_body import CarBody
from test_stuff.colors import StockColor
from test_stuff.draw import Draw

class Simulation:    
    def __init__(self, world_bodies, delta):
        self.world_bodies = world_bodies
        self.delta = delta

    def move_bodies(self):
        for body in self.world_bodies:
            body.move(self.delta)
    
    def draw(self):
        for body in self.world_bodies:
            body.draw()        

def main():
    # Initialise screen
    pygame.init()
    screen_size = (1000, 900)

    # Set where the display will move to
    x, y = 600, 40
    os.environ['SDL_VIDEO_WINDOW_POS']='%d,%d' %(x,y)
    screen = pygame.display.set_mode(screen_size)

    clock = Clock()
    frame_count = 0
    FPS = 100
    UPS = 100
    delta = 1 / UPS

    pygame.display.set_caption('Test car control')

    # Build world.

    origin = Vector2(screen_size[0] / 2, screen_size[1]/ 2)

    car_size = Vector2(16, 28)
    car_scale = 1 # Cambiar esto afecta a la fisica
    car_visual_scale = 2 # Cambiar esto NO afecta a la fisica

    car = CarBody(origin.x, origin.y, 0, 0, car_size.x * car_scale, car_size.y * car_scale, StockColor.CYAN)
    car.visual_scale = car_visual_scale

    world_bodies = [ car ]

    simulation = Simulation(world_bodies, delta)

    # Event loop

    loop_exit = False
    while not loop_exit:
        if frame_count % (FPS // UPS) == 0:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_RIGHT]:
                car.steering_angle += 5 * math.pi / 180
            if keys[pygame.K_LEFT]:
                car.steering_angle -= 5 * math.pi / 180
            if keys[pygame.K_UP]:
                car.braking = False
            if keys[pygame.K_DOWN]:
                car.braking = True

            for event in pygame.event.get():
                if (event.type == pygame.QUIT or
                    event.type == pygame.KEYDOWN and event.key == pygame.K_q):
                    loop_exit = True                
                # if (event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT):
                #     car.steering_angle += 5
                # if (event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT):
                #     car.steering_angle -= 5
                if (event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN):
                    car.braking = True
                if (event.type == pygame.KEYUP and event.key == pygame.K_DOWN):
                    car.braking = False
                if event.type == pygame.MOUSEBUTTONDOWN:                
                    car.braking = True
                if event.type == pygame.MOUSEBUTTONUP:
                    car.braking = False
                if event.type == pygame.MOUSEMOTION:
                    # event.rel is the relative movement of the mouse.
                    mouse_pos = event.pos
                    car.screen_origin = origin
                    car.mouse_position = Vector2(mouse_pos)

        screen.fill((0, 0, 0)) # Clear background

        if frame_count % (FPS // UPS) == 0:
            simulation.move_bodies()

        simulation.draw()

        pygame.display.update()

        frame_count += 1

        clock.tick(FPS)

    pygame.quit()

if __name__ == '__main__':
    main()
