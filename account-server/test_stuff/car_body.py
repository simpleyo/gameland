import numpy as np
import sys
import time
import math
import pygame
from pygame.math import Vector2
from test_stuff.draw import Draw
from test_stuff.colors import StockColor

sign = lambda x: -1 if x < 0 else 1

def degrees(v):
    return v * 180 / math.pi

class CarBody:
    def __init__(self, x, y, vx, vy, rx, ry, col):
        # ATENCION: El sistema de coordenadas utilizado en la simulacion es el mismo que se utiliza para 
        # dibujar las cosas en la pantalla, es decir, el eje -y apunta hacia arriba.

        self.screen_origin = Vector2()

        self.visual_scale = 1

        self.position = Vector2(x, y)
        self.prev_position = Vector2(x, y)
        self.velocity = Vector2(vx, vy)
        self.angular_velocity = 0
        self.angular_acceleration = 0
        self.color = col
        self.radius = Vector2(rx, ry)


        self.braking_force = 1

        self.skid_angle = 0

        self.engine_power = 0              # Fuerza actual del motor del car. Si es negativo significa que va marcha atras.
        self.mouse_position = Vector2()    # Es la posicion del raton que llega del cliente
        self.control_direction = Vector2() # Direccion del car

        self.mass = 1000
        self.inertia = self.mass * (((rx*2) * (rx*2)) + ((ry*2) * (ry*2))) / 12 # I = mass * (a^2 + b^2) / 12 (momento de inercia de una rectangulo que gira alrededor de su centroide)

        self.wheel_base = (ry * 2) * 2 / 3 # Distancia entre los ejes de las ruedas delanteras y traseras. The distance between front and rear axle is known at the wheel_base 
        self.orientation = 1            # Angulo (CW), en radianes, que forma el car con respecto al eje -y
        self.steering_angle = 0         # Angulo (CW), en radianes, que forman las ruedas delanteras con respecto a la orientacion del car

        self.is_moving_reverse = False # Es True si la velocidad frontal es negativa

        self.air_resistance_constant = 0.5
        self.rolling_resistance_constant = 30 * self.air_resistance_constant
        self.brake_constant = 200000
        self.braking = False

        self.cornering_stiffness_constant = 200

        self.rear_lateral_force = None

        print("Car data:")
        print("\tPosition: {}".format(self.position))
        print("\tVelocity: {}".format(self.velocity))
        print("\tAngular velocity: {}".format(self.angular_velocity))
        print("\tWidth: {}".format(rx * 2))
        print("\tHeight: {}".format(ry * 2))
        print("\tMass: {}".format(self.mass))
        print("\tAxles distance: {}".format(self.wheel_base))
        print("\tOrientation: {}".format(self.orientation))
        print("\tSteering angle: {}".format(self.steering_angle))
        print("\tAir resistance constant: {}".format(self.air_resistance_constant))
        print("\tRolling resistance constant: {}".format(self.rolling_resistance_constant))
        print("\tBrake constant: {}".format(self.brake_constant))
        print("\tBraking: {}".format(self.braking))

    def aabb_radius(self):
        return self.radius

    def move(self, delta):

        self.control_direction = self.mouse_position  - self.position
        # self.control_direction = self.mouse_position - self.screen_origin

        # La marcha atras se controla mediante <braking>
        # [
        engine_power_factor = 300
        # engine_power es la velocidad, unidades de distancia por segundo, a la que se
        # desea desplazar el car a la siguiente posicion.
        # La posicion final depende, ademas de engine_power, de la posicion actual, 
        # de la orientacion del car, de steering angle y de delta.
        # La posicion final es una posicion deseada ya lo que se hace no es mover 
        # el car directamente a esa posicion deseada sino que lo que se hace es añadir, a 
        # la velocidad actual del car, la velocidad que seria necesaria, suponiendo que el car tuviera velocidad cero,
        # para alcanzar la posicion deseada en un segundo.
        self.engine_power = engine_power_factor 
        # if self.braking:
        #     self.engine_power = engine_power_factor # -engine_power_factor
        # else:
        #     self.engine_power = engine_power_factor
        # ]

        # Calcula el steering_angle a partir de _control_direction_normalized y _orientation.
        # [
        if True: # USE_MOUSE_INPUT
            control_direction_normalized = self.control_direction.normalize()

            # ATENCION: Vector2.rotate rota grados hacia CCW pero como estamos utilizando coordenadas de pantalla (eje y invertido) el resultado es una rotacion CW.
            # Por lo tanto, si se pasa el parametro negado entonces se estara haciendo una rotacion CCW.
            # Rotando -self.orientation en sentido CW implica cambiar al sistema de referencia donde el car apunta hacia el eje -y.
            u = control_direction_normalized.rotate(degrees(-(self.orientation))) # orientation esta entre [0, 2*pi]
            # u = control_direction_normalized.rotate(degrees(-(self.orientation + self.skid_angle))) # orientation esta entre [0, 2*pi]

            # ATENCION: Llamando a atan2, pasando como parametros las coordenadas (de un punto en coordenadas de pantalla) 
            # invertidas (la x, donde atan2 espera la 'y', y viceversa) y con la 'y' negada, esta devuelve el angulo (CW) 
            # que forma dicho punto con el eje -y (el cual apunta hacia arriba en el sistema de coordenadas de pantalla). 
            # Devuelve un angulo en radianes entre [-pi, pi]
            # angle = math.atan2(x, -y)
            self.steering_angle = math.atan2(u.x, -u.y)
        #]

        # Limita angle a [-max_turn_angle, max_turn_angle]
        # [
        max_turn_angle = math.pi / 4
        angle = self.steering_angle            
        angle = min(max(-max_turn_angle, angle), max_turn_angle)
        self.steering_angle = angle
        # ]      
        
        # Para permitir la marcha atras
        # [
        currentFrontalVector = Vector2(0, -1).rotate(degrees(self.orientation))
        self.currentFrontalVector = currentFrontalVector
        # dot(v, u) = |v| * |u| * cos(a) siendo a el angulo que forman v y u, y siendo v=velocidad y u=currentFrontalVector
        frontal_dir = currentFrontalVector.dot(self.velocity) # frontal_dir sera negativo si el angulo entre la orientacion y la velocidad es mayor que 90 grados

        # local_steering_angle = self.steering_angle # Se utiliza para permitir la marcha atras. Permite modificar el steering_angle que se utiliza en esta funcion pero sin modificar self.steering_angle
        if self.braking: #frontal_dir < 0: #and
            self.braking_force += 10
            # self.steering_angle = -self.steering_angle
        else:
            self.braking_force = 0
        # ]
        
        # Calcula desired_car_location
        # [

        # sn = math.sin(self.orientation)
        # cs = math.cos(self.orientation)

        half_wheel_base = self.wheel_base / 2

        # Rota el punto (0, -half_wheel_base), self.orientation radianes en sentido CW para obtener donde esta la rueda delantera
        front_wheel = self.position + Vector2(0, -half_wheel_base).rotate(degrees(self.orientation)) # (self.position.x + sn * half_wheel_base, self.position.y - cs * half_wheel_base)
        # Rota el punto (0,  half_wheel_base), self.orientation radianes en sentido CW para obtener donde esta la rueda trasera
        back_wheel  = self.position + Vector2(0, half_wheel_base).rotate(degrees(self.orientation)) # (self.position.x - sn * half_wheel_base, self.position.y + cs * half_wheel_base)
        
        # fw = Vector2(0, -half_wheel_base * self.visual_scale).rotate(degrees(self.orientation))
        # bw = Vector2(0,  half_wheel_base * self.visual_scale).rotate(degrees(self.orientation))
        # Draw.circle(self.position + fw, StockColor.GREEN, 3 * int(self.visual_scale + 0.5), 1)
        # Draw.circle(self.position + bw, StockColor.GREEN, 3 * int(self.visual_scale + 0.5), 1)
        # Draw.circle(self.position, StockColor.YELLOW, 3 * int(self.visual_scale + 0.5), 1)

        front_wheel += self.engine_power * delta * Vector2(math.sin(self.orientation + self.steering_angle), -math.cos(self.orientation + self.steering_angle))
        back_wheel  += self.engine_power * delta * Vector2(math.sin(self.orientation), -math.cos(self.orientation)) # El vector (sn, -cs) es el vector (0, -1) rotado self.orientation radianes en sentido CW

        # fw += self.engine_power * delta * Vector2(math.sin(self.orientation + local_steering_angle), -math.cos(self.orientation + local_steering_angle)) * self.visual_scale
        # bw += self.engine_power * delta * Vector2(sn, -cs) * self.visual_scale
        # Draw.circle(self.position + fw, StockColor.GREEN, 3 * int(self.visual_scale + 0.5), 1)
        # Draw.circle(self.position + bw, StockColor.GREEN, 3 * int(self.visual_scale + 0.5), 1)
        # Draw.circle(self.position, StockColor.YELLOW, 3 * int(self.visual_scale + 0.5), 1)

        direc = (back_wheel - front_wheel).normalize()
        desired_car_location = front_wheel + half_wheel_base * direc

        # Draw.circle(desired_car_location, StockColor.YELLOW, 3* int(self.visual_scale + 0.5), 1)

        # ]

        # Calcula desired_car_orientation
        # [
        u = front_wheel - back_wheel
        angle = math.atan2(u.x, -u.y)
        if angle < 0:
            angle += (2 * math.pi)
        desired_car_orientation = angle
        # ]

        position_diff = desired_car_location - self.position # position_diff se puede interpretar como una velocidad en unidades de distancia / delta

        next_angle = self.orientation + self.angular_velocity * delta
        total_rotation = desired_car_orientation - next_angle
        while total_rotation < -math.pi:
            total_rotation += 2 * math.pi
        while total_rotation >  math.pi:
            total_rotation -= 2 * math.pi

        desired_angular_velocity = total_rotation / delta

        # Remove lateral velocity.
        # [

        # ATENCION: Vector2.rotate rota grados hacia CCW pero como estamos utilizando coordenadas de pantalla (eje y invertido) el resultado es una rotacion CW.
        # Por lo tanto, si se pasa el parametro negado entonces se estara haciendo una rotacion CCW.
        # Rotando -self.orientation en sentido CW implica cambiar al sistema de referencia donde el car apunta hacia el eje -y.
        currentRightVector = Vector2(1, 0).rotate(degrees(desired_car_orientation))

        # Draw.line(self.position, self.position + self.velocity, StockColor.YELLOW)

        lateralVelocity = currentRightVector.dot(position_diff) * currentRightVector * delta
        
        lateral_impulse = self.mass * -lateralVelocity
        self.lateral_impulse = lateral_impulse
        # print(lateral_impulse, currentRightVector, self.velocity)

        SKID_FACTOR = 0.03 # Efecto gran deslizamiento con 0.02
        desired_velocity = self.velocity + lateral_impulse / self.mass - SKID_FACTOR * (currentRightVector.dot(self.velocity) * currentRightVector)

        # Draw.line(self.position, self.position + desired_velocity, StockColor.RED)

        # ]

        desired_velocity += position_diff

        # Limita la velocidad
        # [            
        MAX_SPEED = 800

        currentFrontalVector = Vector2(0, -1).rotate(degrees(desired_car_orientation))
        Draw.line(self.position, self.position + currentFrontalVector * 100, StockColor.GRAY)
        # dot(v, u) = |v| * |u| * cos(a) siendo a el angulo que forman v y u, y siendo v=velocidad y u=currentFrontalVector
        frontal_dir = currentFrontalVector.dot(desired_velocity) # frontal_dir sera negativo si el angulo entre la orientacion deseada y la velocidad deseada es mayor que 90 grados
        frontalVelocity = frontal_dir * currentFrontalVector
        
        self.is_moving_reverse = (frontal_dir < 0)

        current_lateral_velocity = (currentRightVector.dot(self.velocity) * currentRightVector)
        Draw.line(self.position, self.position + current_lateral_velocity / 3, StockColor.GREEN)
        # Draw.line(self.position, self.position + lateralVelocity * 200 / delta, StockColor.GREEN)

        if not self.braking or frontal_dir > 0:
            # El target skid angle depende linealmente de la velocidad lateral actual
            # target_skid_angle = sign(self.steering_angle) * lateralVelocity.length() * 2 / delta
            target_skid_angle = sign(self.steering_angle) * current_lateral_velocity.length() * 2 / 700
            target_skid_angle = max(min(target_skid_angle, math.pi), -math.pi)
            SKID_TARGET_CONSTANT = 0.02 # Cuanto mayor es, mas rapido se alcanza el target skid angle
            if frontal_dir > 0:
                self.skid_angle += (target_skid_angle - self.skid_angle) * SKID_TARGET_CONSTANT * max(frontalVelocity.length() / self.radius.y * delta, 1)
        else:
            self.skid_angle *= 0.95 # Elimina progresivamente el skid angle cuando se va marcha atras

        # if not self.braking:
        #     target_skid_angle = sign(self.steering_angle) * current_lateral_velocity.length() * 2 / delta
        #     self.skid_angle += (target_skid_angle - self.skid_angle) * 0.85
        # else:
        #     self.skid_angle *= 0.95

        if frontal_dir < 0:
            if frontalVelocity.length() > (MAX_SPEED / 3):
                desired_velocity += currentFrontalVector * (frontalVelocity.length() - (MAX_SPEED / 3))
        elif frontalVelocity.length() > MAX_SPEED:
            desired_velocity -= currentFrontalVector * (frontalVelocity.length() - MAX_SPEED)

        if self.braking:
            BRAKING_FORCE_CONSTANT = self.braking_force
            desired_velocity -= math.cos(self.steering_angle) * currentFrontalVector * BRAKING_FORCE_CONSTANT * delta * min((2 - (frontalVelocity.length() / MAX_SPEED)) + 0.6, 2)
        # ]

        # Aplica impulsos.
        # [
        self.velocity = desired_velocity

        Draw.line(self.position, self.position + self.velocity / 5, StockColor.YELLOW)

        angular_impulse = self.inertia * desired_angular_velocity
        self.angular_velocity += (1 / self.inertia) * angular_impulse
        # ]

        self.orientation += (self.angular_velocity * delta)

        p = self.position
        v = self.velocity

        self.prev_position = p
        np = p + v * delta
        self.position = np

        return

    def draw(self, col=None):
        self._draw_car()

    def _draw_car(self):

        s = self.visual_scale

        r = Vector2(self.radius * s)

        # cp = Vector2(self.screen_origin)
        cp = Vector2(self.position)

        steering = -self.steering_angle if self.braking and self.is_moving_reverse else self.steering_angle

        self._draw_rotated_rect(cp, r, degrees(self.orientation), Vector2(), StockColor.ORANGE) # draw car body
        Draw.circle(cp + (Vector2(0, 0)).rotate(degrees(self.orientation)), StockColor.YELLOW, 5, 1)

        cp += Vector2(r.y*2/3 * math.sin(self.orientation), -r.y*2/3 * math.cos(self.orientation))

        self._draw_rotated_rect(cp,
            r, degrees(self.orientation + self.skid_angle), Vector2(0, -r.y*2/3)) # draw car body with skid

        wr = Vector2(r.x / 8, r.y / 6) # radio del rect de una rueda

        p1 = Vector2(- wr.x, - wr.y)
        p2 = Vector2(+ wr.x, - wr.y)
        p3 = Vector2(+ wr.x, + wr.y)
        p4 = Vector2(- wr.x, + wr.y)

        # Rueda delantera izquierda

        offset = Vector2(-r.x, -2* r.y / 3)
        t1 = cp + (p1.rotate(degrees(steering)) + offset - Vector2(0, -r.y*2/3)).rotate(degrees(self.orientation + self.skid_angle))
        t2 = cp + (p2.rotate(degrees(steering)) + offset - Vector2(0, -r.y*2/3)).rotate(degrees(self.orientation + self.skid_angle))
        t3 = cp + (p3.rotate(degrees(steering)) + offset - Vector2(0, -r.y*2/3)).rotate(degrees(self.orientation + self.skid_angle))
        t4 = cp + (p4.rotate(degrees(steering)) + offset - Vector2(0, -r.y*2/3)).rotate(degrees(self.orientation + self.skid_angle))

        Draw.lines([t1, t2, t3, t4], self.color)

        # Rueda delantera derecha

        offset = Vector2(+r.x, -2* r.y / 3)
        t1 = cp + (p1.rotate(degrees(steering)) + offset - Vector2(0, -r.y*2/3)).rotate(degrees(self.orientation + self.skid_angle))
        t2 = cp + (p2.rotate(degrees(steering)) + offset - Vector2(0, -r.y*2/3)).rotate(degrees(self.orientation + self.skid_angle))
        t3 = cp + (p3.rotate(degrees(steering)) + offset - Vector2(0, -r.y*2/3)).rotate(degrees(self.orientation + self.skid_angle))
        t4 = cp + (p4.rotate(degrees(steering)) + offset - Vector2(0, -r.y*2/3)).rotate(degrees(self.orientation + self.skid_angle))

        Draw.lines([t1, t2, t3, t4], self.color)

        # Rueda trasera izquierda

        offset = Vector2(-r.x, +2* r.y / 3)
        t1 = cp + (p1 + offset - Vector2(0, -r.y*2/3)).rotate(degrees(self.orientation + self.skid_angle))
        t2 = cp + (p2 + offset - Vector2(0, -r.y*2/3)).rotate(degrees(self.orientation + self.skid_angle))
        t3 = cp + (p3 + offset - Vector2(0, -r.y*2/3)).rotate(degrees(self.orientation + self.skid_angle))
        t4 = cp + (p4 + offset - Vector2(0, -r.y*2/3)).rotate(degrees(self.orientation + self.skid_angle))

        Draw.lines([t1, t2, t3, t4], self.color)

        # Rueda trasera derecha

        offset = Vector2(+r.x, +2* r.y / 3)
        t1 = cp + (p1 + offset - Vector2(0, -r.y*2/3)).rotate(degrees(self.orientation + self.skid_angle))
        t2 = cp + (p2 + offset - Vector2(0, -r.y*2/3)).rotate(degrees(self.orientation + self.skid_angle))
        t3 = cp + (p3 + offset - Vector2(0, -r.y*2/3)).rotate(degrees(self.orientation + self.skid_angle))
        t4 = cp + (p4 + offset - Vector2(0, -r.y*2/3)).rotate(degrees(self.orientation + self.skid_angle))

        Draw.lines([t1, t2, t3, t4], self.color)

        # Dibuja el vector velocidad

        # Draw.line(cp, cp + self.lateralVelocity * 20, StockColor.RED)

        # Dibuja el vector rear_lateral_force

        # Draw.line(cp, cp + self.rear_lateral_force / 200, StockColor.GREEN)

    def _draw_rotated_rect(self, pos, radius, angle, center=Vector2(), col=None):

        # center es el centro de rotacion en coordenadas locales del rect

        v1 = Vector2(- radius.x, - radius.y) - center 
        v2 = Vector2(+ radius.x, - radius.y) - center
        v3 = Vector2(+ radius.x, + radius.y) - center
        v4 = Vector2(- radius.x, + radius.y) - center
        
        v1 = pos + v1.rotate(angle)
        v2 = pos + v2.rotate(angle)
        v3 = pos + v3.rotate(angle)
        v4 = pos + v4.rotate(angle)

        if not col:
            col = self.color

        Draw.lines([v1, v2, v3, v4], col)

