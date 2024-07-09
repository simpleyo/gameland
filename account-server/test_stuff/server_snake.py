import math
import pygame
from pygame.math import Vector2
from .colors import StockColor as Color

class SnakeControlFlag:
    """ ... """
    BOOST = 0x01

class SnakeBodyBase:
    """ ... """
    def __init__(self, x, y):
        self.position = Vector2(x, y)
        self.ref_position = Vector2(x, y)

    def set_position(self, x, y):
        (self.position.x, self.position.y) = (x, y)

    def set_ref_position(self, x, y):
        (self.ref_position.x, self.ref_position.y) = (x, y)

class SnakeHead(SnakeBodyBase):
    """ ... """
    def __init__(self, x, y):
        super().__init__(x, y)

    def draw(self, screen, radius):
        (x, y) = self.position
        # Draw snake head.        
        pygame.draw.circle(screen, Color.RED, (int(x+0.5), int(y+0.5)), radius) 
        pygame.draw.circle(screen, Color.BLACK, (int(x+0.5), int(y+0.5)), radius-2) 
        pygame.draw.circle(screen, Color.RED, (int(x+0.5), int(y+0.5)), radius-4) 
        
class SnakeBody(SnakeBodyBase):
    """ ... """
    def __init__(self, x, y):
        super().__init__(x, y)

    def draw(self, screen, color, radius):
        (x, y) = self.position
        (rx, ry) = self.ref_position

        # Draw ref position.
        # pygame.draw.circle(screen, Color.GREEN, (int(rx), int(ry)), radius) 

        # Draw snake body.
        pygame.draw.circle(screen, color, (int(x+0.5), int(y+0.5)), radius) 

class ServerSnake:
    """ ... """

    SNAKE_DELTA = 1 / 30 # Tiempo maximo que puede durar un step de la snake. En una iteracion pueden haber varios steps.
    INITIAL_SNAKE_RADIUS = 16      # En pixeles.
    INITIAL_BODY_SEPARATION = INITIAL_SNAKE_RADIUS
    # Es igual a (md / INITIAL_BODY_SEPARATION), siendo md la longitud minima que debe tener el lado AC,
    # siendo el triangulo isosceles A,B,C con |AB| = |BC| = INITIAL_BODY_SEPARATION y |AC| = d
    # Si d < md entonces hay que aplicar la restriccion angular.
    # Si ANGULAR_CONSTRAINT_RATIO = 0 entonces se permitiran todos los angulos entre AB y BC
    # Si ANGULAR_CONSTRAINT_RATIO = 1 entonces el angulo minimo sera de 60 grados porque
    #   md = INITIAL_BODY_SEPARATION y entonces |AB| = |BC| = |AC|, es decir, el triangulo A,B,C 
    #   sera equilatero.
    # ANGULAR_CONSTRAINT_RATIO debe ser < 2 porque si es igual a 2 entonces A,B,C estan en linea.
    ANGULAR_CONSTRAINT_RATIO = 1.5
    INITIAL_SPEED = 100     # En pixeles / segundo.
    BOOST_MULT = 4
    INITIAL_NUM_BODIES = 200
    # Maximo angulo de giro por segundo, en grados.
    # En una iteracion concreta: max_turn_angle = MAX_TURN_ANGLE * boost_mult * delta * (INITIAL_BODY_SEPARATION / bodies_separation)
    MAX_TURN_ANGLE = 360

    def __init__(self, x=300, y=400, vx=0, vy=-1 * INITIAL_SPEED, num_bodies=INITIAL_NUM_BODIES):
        self._head = SnakeHead(x, y)
        self._velocity = Vector2(vx, vy)
        self._radius = ServerSnake.INITIAL_SNAKE_RADIUS
        self._bodies_separation = ServerSnake.INITIAL_BODY_SEPARATION

        self._direction = self._velocity.normalize() # Direccion de la snake. Es la posicion del raton que llega del cliente, la cual indica la direccion de la snake
        self._direction_normalized = self._direction.normalize() # Se actualiza siempre que cambia direction
        
        head_position = self._head.position

        self._bodies = []
        for i in range(num_bodies):
            nbp = head_position - (self._direction_normalized * (self._bodies_separation * (i+1)));
            self._bodies.append(SnakeBody(nbp.x, nbp.y))

        # for debug
        self._mouse_pos = (0, 0)

    def draw(self, screen):
        (x, y) = self._head.position
        (vx, vy) = self._velocity
        (mx, my) = self._mouse_pos
        d = Vector2(vx*100, vy*100)
        # rle = d.rotate(-ServerSnake.TURN_DETECTION_ANGLE)

        # Draw snake bodies.
        for i, body in enumerate(reversed(self._bodies)):
            color_a = Color.YELLOW
            color_b = Color.RED
            if len(self._bodies) % 2 == 0:
                if i % 2 != 0:
                    body.draw(screen, color_a, self._radius)
                else:
                    body.draw(screen, color_b, self._radius)
            else:
                if i % 2 == 0:
                    body.draw(screen, color_a, self._radius)
                else:
                    body.draw(screen, color_b, self._radius)

        # Draw snake head.
        self._head.draw(screen, self._radius)

        # Draw debug lines.
        # pygame.draw.aaline(screen, Color.GREEN, [x, y], [x+d.x, x+d.y], True)
        # pygame.draw.aaline(screen, Color.BLUE, [x, y], [mx, my], True)

    def move_v1(self, delta):

        # Modo fijo. La snake siempre pasa por sus referencias.

        # Calcula el desplazamiento que tendra el head con respecto a su posicion actual.
        d = Vector2(self._velocity.x * delta, self._velocity.y * delta)

        np = self._head.position + d  # Nueva posicion de que tendra el head.

        # Calcula el desplazamiento que tendra el head con respecto a su posicion de referencia.
        dr = np - self._head.ref_position

        if dr.length() > self._bodies_separation:
            # Se asume que dr.length() es <= 2 * self._bodies_separation
            # assert dr.length() <= 2 * self._bodies_separation # Esto no se cumple cuando SERVER_UPS es "bajo"

            # La posicion de referencia no debe cambiar en cada iteracion. Solo debe cambiar cuando
            # la cabeza haya avanzado una distancia mayor a bodies_separation desde su posicion de referencia.
            # Cuando eso suceda, se deben mover hacia delante, una distancia de bodies_separation, todas
            # las referencias en el path que definen las propias referencias y la nueva posicion
            # de la cabeza.

            # El segmento actual es [ref_pos(head), np]
            # Hay que mover ref_pos(head) hacia np, una distancia de INITIAL_BODY_SEPARATION.

            dr_len = dr.length()
            u = int(dr_len // self._bodies_separation)
            assert u >= 1
            rm = dr_len - (self._bodies_separation * u)

            new_ref_pos_list = []

            # original_head_ref_pos = Vector2(self._head.ref_position) # Guarda esta posicion.
            # new_head_ref_pos = np + ((original_head_ref_pos - np) / dr_len) * ((self._bodies_separation * 0) + rm)
            # u -= 1
            
            self._bodies.insert(0, self._head)  # Inserta self._head en al principio de self._bodies

            for i in range(u):
                new_ref_pos_list.append(np + ((self._head.ref_position - np) / dr_len) * ((self._bodies_separation * i) + rm))

            # Para i=N-1..u, siendo N = len(bodies), ref_pos(i) = ref_pos(i-u)
            for i in range(len(self._bodies)-1, u-1, -1): # El u-1 indica el final y no esta incluido.
                new_ref_pos_list.insert(1, self._bodies[i-u].ref_position)
            
            del self._bodies[0] # Elimina self._head del principio de self._bodies

            self._head.ref_position = new_ref_pos_list[0]
            for i, rp in enumerate(new_ref_pos_list[1:]):
                self._bodies[i].ref_position = rp

            # # Y ahora hay que asignar a ref_pos(0) = original_head_ref_pos.
            # self._bodies[0].ref_position = original_head_ref_pos

        # Ahora hay que mover la cabeza y los bodies de la snake.
        # El path para mover las posiciones de los bodies de la snake en cada iteracion viene definido
        # por la posicion actual de la cabeza, seguida por la posicion de referencia de la cabeza,
        # seguida por la posicion de referencia de los demas bodies.      
                    
        # El segmento actual es [ref_pos(0), np]
        # pos(head) = np   Mueve la posicion de la head.
        # od es la 'offset distance', es decir, od = length(pos(i) - ref_pos(i)) para los bodies
        #   y od = length(np - self._head.ref_position) para la head
        # od es la misma para todos ellos.
        # Para i=1..N-1, siendo N = len(bodies), pos(i) = ref_pos(i) + (ref_pos(i-1) - ref_pos(i)).nomalize() * od
        # pos(0) = ref_pos(0) + (ref_pos(head) - ref_pos(0)).normalize() * od
        self._head.position = np
        od = (np - self._head.ref_position).length()
        for i, body in enumerate(self._bodies[1:], 1):
            v = (self._bodies[i-1].ref_position - body.ref_position)
            if v.length_squared():
                v = v.normalize()
                body.position = body.ref_position + v * od

        v = (self._head.ref_position - self._bodies[0].ref_position)
        if v.length_squared():
            self._bodies[0].position = self._bodies[0].ref_position + v.normalize() * od

    def move_v2(self, delta):

        # La snake no siempre pasa por sus referencias. Las curvas tienden a cerrarse.

        # Calcula el desplazamiento que tendra el head con respecto a su posicion actual.
        d = Vector2(self._velocity.x * delta, self._velocity.y * delta)

        np = self._head.position + d  # Nueva posicion de que tendra el head.
        
        # print("A")

        # Calcula el desplazamiento que tendra el head con respecto a su posicion de referencia.
        dr = np - self._head.ref_position

        if dr.length() > self._bodies_separation:

            # print("B")

            # La posicion de referencia no debe cambiar en cada iteracion. Solo debe cambiar cuando
            # la cabeza haya avanzado una distancia mayor a bodies_separation desde su posicion de referencia.
            # Cuando eso suceda, se deben mover hacia delante, una distancia de bodies_separation, todas
            # las referencias en el path que definen las propias referencias y la nueva posicion
            # de la cabeza.

            # Precondiciones:
            # Asume que todas las referencias consecutivas estan separadas por una distancia igual a INITIAL_BODY_SEPARATION.
            # Asume que, dados dos segmentos consecutivos (en el path que forman las referencias) estos nunca
            # se superponen, es decir, se asume que segmentos consecutivos nunca se pliegan formando un angulo nulo.

            # El segmento actual es [np, ref_pos(head)]

            new_head_ref_pos = np

            # Hay que mover ref_pos(0) desde np, por el segmento actual [np, ref_pos(head)], una distancia de INITIAL_BODY_SEPARATION.
            
            # Como dr.length() > INITIAL_BODY_SEPARATION es seguro que new_ref_pos(0) estara en el segmento actual.

            new_ref_pos_list = []

            a = np  # source
            b = self._head.ref_position # dest
            rm = dr.length()    # remaining distance

            # Calcula todas las nuevas ref_pos(i) que estan en el segmento [a, b] y las inserta en new_ref_pos_list
            # En rm quedara la distancia (que es menor que INITIAL_BODY_SEPARATION) que sobra.
            num_bodies = len(self._bodies)

            while len(new_ref_pos_list) < num_bodies:
                v = (b - a)
                v_len = v.length()
                new_ref_pos_list.append(a + v.normalize() * self._bodies_separation)
                rm -= self._bodies_separation
                a = new_ref_pos_list[-1]
                if rm < self._bodies_separation:
                    break

            # Al menos ref_pos(0) se debe haber insertado en new_ref_pos_list
            assert new_ref_pos_list # len(new_ref_pos_list) > 0

            # Mueve hacia delante, una distancia de INITIAL_BODY_SEPARATION, todas
            # las referencias en el path que definen las propias referencias.

            if len(new_ref_pos_list) == 1:
                a = self._head.ref_position
                b = self._bodies[0].ref_position
                k = -1
            else: # len(new_ref_pos_list) > 1
                a = self._bodies[0].ref_position
                b = self._bodies[1].ref_position
                k = 0

            # En cada iteracion inserta la ref_pos(k+2)
            while len(new_ref_pos_list) < len(self._bodies):
                v = (b - a)
                # Inserta nueva ref_pos
                new_ref_pos_list.append(a + v.normalize() * (self._bodies_separation - rm))

                k += 1
                if k == (len(self._bodies) - 1):
                    break

                a = self._bodies[k].ref_position
                b = self._bodies[k+1].ref_position

            # Aplica restricciones de distancia a las posiciones en new_ref_pos_list
            # Entre una y la siguiente debe haber una distancia igual a INITIAL_BODY_SEPARATION.

            len_new_ref_pos_list = len(new_ref_pos_list)
            i = 0
            while i < len_new_ref_pos_list-1:
                a = new_ref_pos_list[i]
                b = new_ref_pos_list[i+1]
                v = (b - a)
                ds = v.length()
                if ds == 0:
                    # Caso que nunca deberia pasar ya que 'a' nunca deberia poder ser igual a 'b'.
                    # Para que este caso nunca ocurra es necesario que, dados dos segmentos
                    # consecutivos (en el path que forman las referencias) estos nunca
                    # se superpongan.
                    v = (1, 0)
                
                new_ref_pos_list[i+1] = a + v.normalize() * self._bodies_separation # new b

                i += 1

            # Actualiza self._head.ref_position y self._bodies con new_head_ref_pos y new_ref_pos_list
            self._head.ref_position = new_head_ref_pos
            for i, body in enumerate(self._bodies):
                body.ref_position = new_ref_pos_list[i]

        # Ahora hay que mover la cabeza y los bodies de la snake.
        # El path para mover las posiciones de los bodies de la snake en cada iteracion viene definido
        # por la posicion actual de la cabeza, seguida por la posicion de referencia de la cabeza,
        # seguida por la posicion de referencia de los demas bodies.      
                    
        # El segmento actual es [ref_pos(0), np]
        # pos(head) = np   Mueve la posicion de la head.
        # od es la 'offset distance', es decir, od = length(pos(i) - ref_pos(i)) para los bodies
        #   y od = length(np - self._head.ref_position) para la head
        # od es la misma para todos ellos.
        # Para i=1..N-1, siendo N = len(bodies), pos(i) = ref_pos(i) + (ref_pos(i-1) - ref_pos(i)).nomalize() * od
        # pos(0) = ref_pos(0) + (ref_pos(head) - ref_pos(0)).normalize() * od
        self._head.position = np
        od = (np - self._head.ref_position).length()
        for i, body in enumerate(self._bodies[1:], 1):
            v = (self._bodies[i-1].ref_position - body.ref_position)
            if v.length_squared():
                v = v.normalize()
                body.position = body.ref_position + v * od

        v = (self._head.ref_position - self._bodies[0].ref_position)
        if v.length_squared():
            self._bodies[0].position = self._bodies[0].ref_position + v.normalize() * od      

    def move_v3(self, delta):
    
        # Calcula el desplazamiento que tendra el head con respecto a su posicion actual.
        d = Vector2(self._velocity.x * delta, self._velocity.y * delta)

        np = self._head.position + d  # Nueva posicion de que tendra el head.
        
        len_d = d.length()

        # La nueva pos(0) se calcula avanzando INITIAL_BODY_SEPARATION desde np, por el segmento actual [np, pos(head)],
        # una distancia de INITIAL_BODY_SEPARATION.
        # Si len_d >= INITIAL_BODY_SEPARATION es seguro que new_pos(0) estara en el segmento actual.

        new_pos_list = []

        a = np  # source
        b = self._head.position # dest
        rm = len_d    # remaining distance

        # Calcula todas las nuevas pos(i) que estan en el segmento [a, b] y las inserta en new_pos_list
        # En rm quedara la distancia (que es menor que INITIAL_BODY_SEPARATION) que sobra.
        while rm >= self._bodies_separation:
            v = (b - a)
            v_len = v.length()
            new_pos_list.append(a + v.normalize() * self._bodies_separation)
            rm -= self._bodies_separation
            a = new_pos_list[-1]

        if len(new_pos_list) == 0:
            a = self._head.position
            b = self._bodies[0].position
            k = -1
        else: # len(new_pos_list) > 0
            a = self._bodies[0].position
            b = self._bodies[1].position
            k = 0

        while len(new_pos_list) < len(self._bodies):
            v = (b - a)
            new_pos_list.append(a + v.normalize() * (self._bodies_separation - rm))       

            k += 1
            if k == (len(self._bodies) - 1):
                break

            a = self._bodies[k].position
            b = self._bodies[k+1].position

        # Aplica restriccion de distancia entre np y new_pos_list[0]
        # Aplica restriccion de distancia a las posiciones en new_pos_list
        # Entre una y la siguiente debe haber una distancia igual a INITIAL_BODY_SEPARATION.

        i = 0
        a = np
        b = new_pos_list[0]

        len_new_pos_list = len(new_pos_list)
        while i < len_new_pos_list:
            v = (b - a)
            ds = v.length()
            if ds == 0: # Caso extraño que nunca deberia pasar.
                v = (1, 0)

            new_pos_list[i] = a + v.normalize() * self._bodies_separation

            a = b
            if i < len_new_pos_list-1:
                b = new_pos_list[i+1]

            i += 1

        # Actualiza las posiciones.

        self._head.position = np
        for i, body in enumerate(self._bodies):
            body.position = new_pos_list[i]

    def move_v4(self, delta):
    
        # Igual que move_v2 pero con restricciones angulares.

        # Calcula el desplazamiento que tendra el head con respecto a su posicion actual.
        d = Vector2(self._velocity.x * delta, self._velocity.y * delta)

        np = self._head.position + d  # Nueva posicion de que tendra el head.
        
        # print("A")

        # Calcula el desplazamiento que tendra el head con respecto a su posicion de referencia.
        dr = np - self._head.ref_position

        if dr.length() > self._bodies_separation:

            # print("B")

            # La posicion de referencia no debe cambiar en cada iteracion. Solo debe cambiar cuando
            # la cabeza haya avanzado una distancia mayor a bodies_separation desde su posicion de referencia.
            # Cuando eso suceda, se deben mover hacia delante, una distancia de bodies_separation, todas
            # las referencias en el path que definen las propias referencias y la nueva posicion
            # de la cabeza.

            # Precondiciones:
            # Asume que todas las referencias consecutivas estan separadas por una distancia igual a INITIAL_BODY_SEPARATION.
            # Asume que, dados dos segmentos consecutivos (en el path que forman las referencias) estos nunca
            # se superponen, es decir, se asume que segmentos consecutivos nunca se pliegan formando un angulo nulo.

            # El segmento actual es [np, ref_pos(head)]

            new_head_ref_pos = np

            # Hay que mover ref_pos(0) desde np, por el segmento actual [np, ref_pos(head)], una distancia de INITIAL_BODY_SEPARATION.
            
            # Como dr.length() > INITIAL_BODY_SEPARATION es seguro que new_ref_pos(0) estara en el segmento actual.

            new_ref_pos_list = []

            a = np  # source
            b = self._head.ref_position # dest
            rm = dr.length()    # remaining distance

            # Calcula todas las nuevas ref_pos(i) que estan en el segmento [a, b] y las inserta en new_ref_pos_list
            # En rm quedara la distancia (que es menor que INITIAL_BODY_SEPARATION) que sobra.
            num_bodies = len(self._bodies)

            while len(new_ref_pos_list) < num_bodies:
                v = (b - a)
                v_len = v.length()
                new_ref_pos_list.append(a + v.normalize() * self._bodies_separation)
                rm -= self._bodies_separation
                a = new_ref_pos_list[-1]
                if rm < self._bodies_separation:
                    break

            # Al menos ref_pos(0) se debe haber insertado en new_ref_pos_list
            assert new_ref_pos_list # len(new_ref_pos_list) > 0

            # Mueve hacia delante, una distancia de INITIAL_BODY_SEPARATION, todas
            # las referencias en el path que definen las propias referencias.

            if len(new_ref_pos_list) == 1:
                a = self._head.ref_position
                b = self._bodies[0].ref_position
                k = -1
            else: # len(new_ref_pos_list) > 1
                a = self._bodies[0].ref_position
                b = self._bodies[1].ref_position
                k = 0

            # En cada iteracion inserta la ref_pos(k+2)
            while len(new_ref_pos_list) < len(self._bodies):
                v = (b - a)
                # Inserta nueva ref_pos
                new_ref_pos_list.append(a + v.normalize() * (self._bodies_separation - rm))

                k += 1
                if k == (len(self._bodies) - 1):
                    break

                a = self._bodies[k].ref_position
                b = self._bodies[k+1].ref_position

            # Aplica restricciones de distancia a las posiciones en new_ref_pos_list
            # Entre una y la siguiente debe haber una distancia igual a INITIAL_BODY_SEPARATION.

            len_new_ref_pos_list = len(new_ref_pos_list)
            i = 0
            while i < len_new_ref_pos_list-1:
                if i > 0:
                    a = new_ref_pos_list[i-1]
                b = new_ref_pos_list[i]
                c = new_ref_pos_list[i+1]
                v = (c - b)
                ds = v.length()
                if ds == 0:
                    # Caso que nunca deberia pasar ya que 'a' nunca deberia poder ser igual a 'b'.
                    # Para que este caso nunca ocurra es necesario que, dados dos segmentos
                    # consecutivos (en el path que forman las referencias) estos nunca
                    # se superpongan.
                    assert False
                    v = (1, 0)

                new_ref_pos_list[i+1] = b + v.normalize() * self._bodies_separation # new c

                # Aplica recorte angular.
                # if i > 0:
                #     v = (c - a)
                #     ds = v.length()
                #     if ds < self._bodies_separation * 1.5:
                #         ms = 0.5 * ds
                #         c = a + v.normalize() * ms
                #         v = (c - b)
                #         ds = v.length()
                #         if ds == 0:
                #             assert False
                #             v = (1, 0)
                #         new_ref_pos_list[i+1] = b + v.normalize() * self._bodies_separation

                # Aplica la restriccion angular.
                if i > 0:
                    v = (c - a)
                    ds = v.length()
                    ms = self._bodies_separation * ServerSnake.ANGULAR_CONSTRAINT_RATIO # min size
                    if ds < ms:
                        if ds == 0:
                            assert False
                            v = (1, 0)
                        c = a + v.normalize() * ms
                        v = (c - b)
                        ds = v.length()
                        if ds == 0:
                            assert False
                            v = (1, 0)
                        new_ref_pos_list[i+1] = b + v.normalize() * self._bodies_separation

                i += 1

            # Actualiza self._head.ref_position y self._bodies con new_head_ref_pos y new_ref_pos_list
            self._head.ref_position = new_head_ref_pos
            for i, body in enumerate(self._bodies):
                body.ref_position = new_ref_pos_list[i]

        # Ahora hay que mover la cabeza y los bodies de la snake.
        # El path para mover las posiciones de los bodies de la snake en cada iteracion viene definido
        # por la posicion actual de la cabeza, seguida por la posicion de referencia de la cabeza,
        # seguida por la posicion de referencia de los demas bodies.      
                    
        # El segmento actual es [ref_pos(0), np]
        # pos(head) = np   Mueve la posicion de la head.
        # od es la 'offset distance', es decir, od = length(pos(i) - ref_pos(i)) para los bodies
        #   y od = length(np - self._head.ref_position) para la head
        # od es la misma para todos ellos.
        # Para i=1..N-1, siendo N = len(bodies), pos(i) = ref_pos(i) + (ref_pos(i-1) - ref_pos(i)).nomalize() * od
        # pos(0) = ref_pos(0) + (ref_pos(head) - ref_pos(0)).normalize() * od
        self._head.position = np
        od = (np - self._head.ref_position).length()
        for i, body in enumerate(self._bodies[1:], 1):
            v = (self._bodies[i-1].ref_position - body.ref_position)
            if v.length_squared():
                v = v.normalize()
                body.position = body.ref_position + v * od

        v = (self._head.ref_position - self._bodies[0].ref_position)
        if v.length_squared():
            self._bodies[0].position = self._bodies[0].ref_position + v.normalize() * od     

    def move(self, delta):

        # Realiza una iteracion de la snake.
        
        do_move = self.move_v4

        if (delta / ServerSnake.SNAKE_DELTA) > 1:
            steps = int((delta // ServerSnake.SNAKE_DELTA) + 1)
        else:
            steps = 1
        # print(steps)
        if steps > 1:
            iter_delta = delta / steps
            for i in range(steps):
                do_move(iter_delta)
        else:
            if delta > 0:
                do_move(delta)

    def update(self, delta, mouse_pos, boost):

        control_flags = 0

        ### Activa control_flags si hay boost.

        if boost:
            control_flags |= SnakeControlFlag.BOOST

        ### Actualiza _direction

        (mx, my) = mouse_pos

        head_position = self._head.position
        (self._direction.x, self._direction.y) = (mx - head_position.x, my - head_position.y)
        if self._direction.length() > 0:
            self._direction_normalized = self._direction.normalize()
        else:
            self._direction_normalized = self._direction

        current_velocity = Vector2(self._velocity)

        ### Activa control_flags si hay giro.

        angle0 = math.atan2(current_velocity.y, current_velocity.x)
        angle1 = math.atan2(self._direction_normalized.y, self._direction_normalized.x)

        if angle0 < 0:
            angle0 = 2 * math.pi - (-angle0)
        if angle1 < 0:
            angle1 = 2 * math.pi - (-angle1)

        angle = angle1 - angle0
        if angle > math.pi:
            angle = -(2 * math.pi) + angle
        if angle < -math.pi:
            angle = (2 * math.pi) + angle

        angle = angle * 180 / math.pi # Convierte angle a grados.

        ### Aqui ya estan disponibles: (control_flags, angle)
        ### angle, en grados, que representa el cambio de direccion de la snake.
        ### Actualiza _velocity

        boost_mult = ServerSnake.BOOST_MULT if (control_flags & SnakeControlFlag.BOOST) else 1

        # El maximo angulo de giro por segundo es proporcional al boost_mult e inversamente
        # proporcional a la separacion entre bodys de la snake. Cuanto mas rapido avanza la snake
        # mayor es el angulo que puede girar en una iteracion.
        
        max_turn_angle = ServerSnake.MAX_TURN_ANGLE * boost_mult * delta * (ServerSnake.INITIAL_BODY_SEPARATION / self._bodies_separation)

        # Limita angle a [-max_turn_angle, max_turn_angle]
        angle = min(max(-max_turn_angle, angle), max_turn_angle)
                
        v = Vector2(self._velocity.normalize() * ServerSnake.INITIAL_SPEED * boost_mult)
        v.rotate_ip(angle)

        (self._velocity.x, self._velocity.y) = (v.x, v.y)

        ### Mueve la snake

        self.move(delta)
        
        self._mouse_pos = mouse_pos # for debug
