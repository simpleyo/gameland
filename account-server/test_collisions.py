import math
from copy import deepcopy
import pygame
from pygame.time import Clock
from pygame.math import Vector2
from pygame.locals import *
from test_stuff.collision_body import RectBody, CircleBody
from test_stuff.colors import StockColor
from test_stuff.draw import Draw

class CollisionType:
    AABB_VS_WORLD_LIMIT = 0
    AABB_VS_AABB = 1
    CIRCLE_VS_AABB = 2
    CIRCLE_VS_CIRCLE = 3

class Simulation:
    """ La deteccion de colisiones entre bodies se realiza a posteriori, es decir,
    se detectan una vez que los bodies han sido movidos. Para la deteccion se utilizan
    las posiciones actuales y previas de los bodies.
    El metodo solve_collisions(delta, world_bodies) se encarga de detectar las colisiones
    que se producen en el intervalo de tiempo [time, time+delta], siendo time el tiempo en
    que el body estaba en su prev_position y time+delta el tiempo en el que esta en su
    position. Primero detecta las colisiones, de cada uno de los bodies en world_bodies,
    con los limites del mundo y luego detecta las colisiones, de cada uno de ellos,
    con el resto.
    Las colisiones detectadas por solve_collisions son insertadas en una
    lista, ordenadas por tiempo de la colision.
    Este metodo de deteccion de colisiones asume que los bodies no cambian su velocidad
    durante el intervalo [time, time+delta] y que siguen existiendo despues de cualquier
    colision.

    La resolucion de colisiones consiste en recorrer la lista de colisiones, la cual
    esta ordenada por tiempo de colision, y, para cada una de ellas:
        - Si es una colision contra los limites del mundo entonces se modifica su velocidad y
            su posicion (para que el body vuelva a estar contenido en el mundo).
            Siendo t0 el tiempo de colision, es decir, el body que colisiona contra un
            solo limite del mundo solo avanza en el tiempo desde time hasta time+t0.
            Para un body que se mueva relativamente rapido puede suceder que en un
            tiempo delta pase, de estar dentro del mundo, a estar fuera de el, tocando
            uno de los 4 cuadrantes de las esquinas.
            En ese caso, se modifica la posicion del body situandolo dentro del mundo,
            pegado a una de las esquinas del este con la velocidad corregida,
            no respetandose la trayectoria "normal" del body, el cual deberia haber
            rebotado contra las paredes en vez de ser movido a una esquina.
        - Si es una colision entre bodies no se hace nada.

     """

    def __init__(self, world_origin, world_radius, world_bodies, delta):
        self.world_origin = world_origin
        self.world_radius = world_radius
        self.world_bodies = world_bodies
        origin = world_origin
        radius = world_radius
        self.world_wall_bodies = [
            RectBody(origin.x-radius*2, origin.y, 0, 0, radius, radius, StockColor.GREEN),
            RectBody(origin.x+radius*2, origin.y, 0, 0, radius, radius, StockColor.GREEN),
            RectBody(origin.x, origin.y-radius*2, 0, 0, radius, radius, StockColor.GREEN),
            RectBody(origin.x, origin.y+radius*2, 0, 0, radius, radius, StockColor.GREEN)
        ]        

        self.delta = delta
        self.collisions = []
        self.collisions_count = 0 # for debug
        self.debug_bodies = []  # Cada entrada es [frames, color, body, position]

    def _closest_point_on_line(self, lx1, ly1, lx2, ly2, x0, y0):
        A1 = ly2 - ly1
        B1 = lx1 - lx2
        C1 = (ly2 - ly1)*lx1 + (lx1 - lx2)*ly1
        C2 = -B1*x0 + A1*y0
        det = A1*A1 - -B1*B1
        cx = 0
        cy = 0
        if det != 0:
            cx = ((A1*C1 - B1*C2)/det)
            cy = ((A1*C2 - -B1*C1)/det)
        else:
            cx = x0
            cy = y0

        return Vector2(cx, cy)

    def _check_world_limits(self, a):
        """ Comprueba si a (un body) esta dentro de los limites del mundo.
        Devuelve el desplazamiento necesario para que body este dentro de los
        limites del mundo. Se asume que el radio del aabb del body cabe dentro del mundo. 
        Los limites son (x, y) = ([-radius, +radius], [-radius, +radius])"""
        o = self.world_origin
        wr = self.world_radius

        (w1x, w1y) = (o.x - wr, o.y - wr)
        (w2x, w2y) = (o.x + wr, o.y + wr)

        ra = a.aabb_radius()

        assert ra.x < wr
        assert ra.y < wr

        (pa1x, pa1y) = a.prev_position - ra
        (pa2x, pa2y) = a.prev_position + ra

        (a1x, a1y) = a.position - ra
        (a2x, a2y) = a.position + ra

        (vax, vay) = (a.position - a.prev_position) / self.delta

        (dx, dy) = (0, 0)
        (tx, ty) = (None, None)
         
        if a1x < w1x:
            dx = w1x - a1x
            tx = (w1x - pa1x) / vax
        elif a2x > w2x:
            dx = w2x - a2x
            tx = (w2x - pa2x) / vax

        if a1y < w1y:
            dy = w1y - a1y
            ty = (w1y - pa1y) / vay
        elif a2y > w2y:
            dy = w2y - a2y
            ty = (w2y - pa2y) / vay

        if tx is not None or ty is not None:
            if tx is not None and ty is not None:
                t = min(tx, ty)
            else:
                t = tx if tx is not None else ty
        else:
            t = None

        if t is None:
            assert dx == 0 and dy == 0

        return (t, dx, dy)

    def _check_static_circles_collide(self, x1, y1, r1, x2, y2, r2):
        return abs((x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2)) < ((r1 + r2) * (r1 + r2))

    def _circle_vs_circle_collide(self, ha, hb):
        # difference vector of the 2 circles' positions
        cdiff = hb.prev_position - ha.prev_position

        # c the squared distance between circles minus the squared sum of their radii
        # this offers a means to check for intersection at the start of the interval
        # without making an expensive square root call
        #
        # ie: if the sum of the circles' radii squared > the distance between them squared,
        # they are overlapping.
        c = cdiff.dot(cdiff) - (ha.radius + hb.radius) ** 2
        if c < 0:
            # initial overlap condition- return with time 0
            t = 0
            return t

        # difference between circles' velocities
        vdiff = hb.velocity - ha.velocity

        a = vdiff.dot(vdiff)
        if a < 0.0000001:
            return None # circles not moving relative each other

        b = vdiff.dot(cdiff)
        if b >= 0:
            return None # circles moving apart        

        d = b * b - a * c
        if d < 0:
            return None # no solution to the quadratic equation- circles don't intersect

        # evaluate the time of collision
        t = (-b - math.sqrt(d)) / a
        if t <= self.delta:
            return t
        else:
            return None

    def _circle_vs_circle_collide_deprecated(self, a, b):
        """ Comprueba si a y b colisionan en el intervalo de tiempo [0, delta].
        a, b son dos circulos dinamicos con velocidades va y vb.
        El caso de que no haya colision en el intervalo [0, delta] se devuelve None.
        El caso de colision en el intervalo [0, delta] se devuelve el tiempo en el
        que sucedio la colision. En el caso de que a y b se esten solapando, en el tiempo 0,
        se devuelve tiempo 0. """

        swap_bodies = False

        if a.static and b.static:
            ra = a.radius
            rb = b.radius
            (ax, ay) = a.position
            (bx, by) = b.position
            if self._check_static_circles_collide(ax, ay, ra, bx, by, rb):
                # initial overlap condition. return with time 0
                return 0 # (-1000000, 1000000)
        elif not a.static and b.static:
            pass
        elif a.static and not b.static:
            (a, b) = (b, a)
            swap_bodies = True

        ra = a.radius
        rb = b.radius
        (ax, ay) = a.position
        (bx, by) = b.position
        (pax, pay) = a.prev_position
        (pbx, pby) = b.prev_position
        
        (vax, vay) = (a.position - a.prev_position) / self.delta
        (vbx, vby) = (b.position - b.prev_position) / self.delta

        # Cambia de sistema de referencia.
        # Esto se puede hacer porque ambos circles se mueven a velocidad constante.
        # Ahora b es considerado como un body
        # fijo (vb = (0,0)), el cual es el nuevo origen de coordenadas.
        # ATENCION: El cambio de sistema de referencia provoca que la precision
        #   sea menor cuando se calcula una posicion (dado un t)
        #   utilizando la velocidad original.

        (nbx, nby) = (bx - pbx, by - pby)
        (pax, pay) = (pax - pbx, pay - pby)
        (vax, vay) = (vax - vbx, vay - vby)

        # Si la velocidad relativa de a con respecto a b es nula entonces se resuleve
        # la colision como si ambos bodies fueran estaticos.
        if vax == 0 and vay == 0:
            if self._check_static_circles_collide(ax, ay, ra, bx, by, rb):
                # initial overlap condition. return with time 0
                return 0 # (-1000000, 1000000)

        d = self._closest_point_on_line(pax, pay, pax + vax, pay + vay, nbx, nby)
        closest_dist_sq = (nbx - d.x)**2 + (nby - d.y)**2
        if closest_dist_sq <= (ra + rb)**2:
            # a collision has occurred
            backdist = math.sqrt((ra + rb)**2 - closest_dist_sq)
            movement_vector_length = math.sqrt(vax**2 + vay**2)
            cx = d.x - backdist * (vax / movement_vector_length)
            cy = d.y - backdist * (vay / movement_vector_length)
            ecx = d.x + backdist * (vax / movement_vector_length)
            ecy = d.y + backdist * (vay / movement_vector_length)

            # Restaura el sistema de referencia original.
            # (cx, cy) = (cx + pbx, cy + pby)
            # (ecx, ecy) = (ecx + pbx, ecy + pby)

            # (pax, pay) = a.prev_position
            # (vax, vay) = (vax + vbx, vay + vby)

            if vax != 0:
                t0 = (cx - pax) / vax
                t1 = (ecx - pax) / vax
                if vay != 0:
                    nt0 = (cy - pay) / vay
                    if t0 != nt0:
                        pass
                
                # if t0 >= 0 and t0 <= self.delta:
                #     # Se pierde precision
                #     # va = (a.position - a.prev_position) / self.delta
                #     # na_pos = a.prev_position + va * t0

                #     # La precision es mejor si se utiliza va antes de volver al marco
                #     # de referencia original.
                #     na_pos = (Vector2(pax, pay) +  Vector2(vax, vay) * t0) + (pbx, pby)
                #     print((na_pos - b.position).length(), ra + rb)

            elif vay != 0:
                t0 = (cy - pay) / vay
                t1 = (ecy - pay) / vay
                if vax != 0:
                    nt0 = (cx - pax) / vax
                    if t0 != nt0:
                        pass
            else:
                # a no es estatico, por lo tanto, va != (0, 0)
                assert False and "Este caso no se puede dar."
                
            if t0 > self.delta or t1 < 0:
                pass    # no collision has occurred
            else:
                return t0 # max(0, t0) # (t0, t1)

        else:            
            pass    # no collision has occurred
        
        return None

    def _static_circle_vs_aabb_collide(self, a, b):
        assert isinstance(a, CircleBody)

        pt = Vector2(a.position)
        ra = a.radius
        rb = b.aabb_radius()
        (bx1, by1) = b.position - (rb.x, rb.y)
        (bx2, by2) = b.position + (rb.x, rb.y)

        if pt.x > bx2:
            pt.x = bx2
        if pt.x < bx1:
            pt.x = bx1
        if pt.y > by2:
            pt.y = by2
        if pt.y < by1:
            pt.y = by1

        if (pt - a.position).length_squared() < (a.radius**2):
            return True

        return False

    def _aabb_vs_aabb_collide(self, a, b):
        """ Comprueba si a y b colisionan en el intervalo de tiempo [0, delta].
        a, b son dos aabb dinamicos con velocidades va y vb.
        El caso de que no haya colision en el intervalo [0, delta] se devuelve None.
        El caso de colision en el intervalo [0, delta] se devuelve el tiempo en el
        que sucedio la colision. En el caso de que a y b se esten solapando, en el tiempo 0,
        se devuelve tiempo 0. """

        ra = a.aabb_radius()
        rb = b.aabb_radius()
        (ax1, ay1) = a.prev_position - (ra.x, ra.y)
        (ax2, ay2) = a.prev_position + (ra.x, ra.y)
        (bx1, by1) = b.prev_position - (rb.x, rb.y)
        (bx2, by2) = b.prev_position + (rb.x, rb.y)

        (vax, vay) = (a.position - a.prev_position) / self.delta
        (vbx, vby) = (b.position - b.prev_position) / self.delta

        ix = None
        iy = None

        (rt0, rt1) = (1, -1)

        if vax != vbx:
            t1=(bx1-ax2)/(vax-vbx)
            t2=(bx2-ax1)/(vax-vbx)
            ix=(t1,t2) if t2 >= t1 else (t2,t1)

        if vay != vby:
            u1=(by1-ay2)/(vay-vby)
            u2=(by2-ay1)/(vay-vby)
            iy=(u1,u2) if u2 >= u1 else (u2,u1)

        if ix and iy:
            (t1, t2) = ix
            (u1, u2) = iy
            if u1 > t2 or u2 < t1:
                pass
            else:
                (rt0, rt1) = (max(t1, u1), min(t2, u2))
        elif ix:
            if ay1 > by2 or ay2 < by1:
                pass
            else:
                (rt0, rt1) = ix
        elif iy:
            if ax1 > bx2 or ax2 < bx1:
                pass
            else:
                (rt0, rt1) = iy
        else:
            if ax1 > bx2 or ax2 < bx1 or ay1 > by2 or ay2 < by1:
                pass
            else:
                (rt0, rt1) = (0, self.delta) # (-1000000, 1000000)

        if rt0 <= rt1:
            if rt0 > self.delta or rt1 < 0:
                pass    # no collision has occurred
            else:
                return rt0 # max(0, rt0)

        return None #(1, -1)

    def _collide(self, a, b):
        collision = False
        if isinstance(a, CircleBody) and isinstance(b, CircleBody):
            ct = CollisionType.CIRCLE_VS_CIRCLE
            t = self._circle_vs_circle_collide(a, b)
            if t is not None:
                collision = True
        else:
            ct = CollisionType.AABB_VS_AABB
            t = self._aabb_vs_aabb_collide(a, b)
            if t is not None:
                collision = True

        return (t, ct, (a, b)) if collision else None

    def _solve_world_limits(self):
        # Las colisiones con los limites del mundo deben resolverse antes de resolver
        # las colisiones entre bodies.
        # Esto debe ser asi porque los limites del mundo determinan las posiciones
        # validas que puede tener un body en un momento dado.

        for body in self.world_bodies:
            r = self._check_world_limits(body)
            if r:
                (t, dx, dy) = r
                if dx or dy:
                    self.collisions.append((t, CollisionType.AABB_VS_WORLD_LIMIT, (body, (dx, dy))))

    def solve_collisions(self):
        """ Detecta colisiones entre cada unos de los world_bodies y los world_wall_bodies y
        entre cada uno de los world_bodies y el resto de world_bodies. """

        self.collisions.clear()

        # Detecta las colisiones.

        self._solve_world_limits()

        for i, a in enumerate(self.world_bodies):
            for b in self.world_bodies[i+1:]:
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

            self.collisions_count += 1
            if show_info:
                cts = "AABB_VS_WORLD_LIMIT" if ct == CollisionType.AABB_VS_WORLD_LIMIT else \
                    "AABB_VS_AABB" if ct == CollisionType.AABB_VS_AABB else \
                    "CIRCLE_VS_CIRCLE" if ct == CollisionType.CIRCLE_VS_CIRCLE else ""
                print("Collision: {} Type: {} Time: {}".format(self.collisions_count, cts, t))

    def move_bodies(self):
        for body in self.world_bodies:
            body.move(self.delta)
    
    def draw(self):
        self.draw_world_limits()
        self.draw_debug_bodies()
        for body in self.world_bodies:
            body.draw()        

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

    pygame.display.set_caption('Test collisions')

    # Build world.

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
        RectBody(origin.x, origin.y, 430, 700,  32, 132, StockColor.CYAN),
        RectBody(origin.x, origin.y, 500, 100,  32, 32, StockColor.CYAN),
        RectBody(origin.x, origin.y, 200, 200,  32, 32, StockColor.CYAN),
        RectBody(origin.x, origin.y, 50, 100,  128, 32, StockColor.CYAN),
        # RectBody(origin.x, origin.y, 100, 70,  128, 32, StockColor.CYAN),
    ]

    simulation = Simulation(origin, world_radius, world_bodies, delta)

    # Event loop

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return

        screen.fill((0, 0, 0)) # Clear background

        simulation.move_bodies()

        simulation.solve_collisions()

        simulation.draw()

        pygame.display.update()

        clock.tick(FPS)


if __name__ == '__main__':
    main()
