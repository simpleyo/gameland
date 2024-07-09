from Box2D.examples.framework import (Framework, Keys, main)
from pygame.math import Vector2
import math

degrees = math.degrees

SCALE = 0.5

class TDTire(object):

    def __init__(self, car, max_forward_speed=100.0,
                 max_backward_speed=-250, max_drive_force=100,
                 max_lateral_impulse=5,
                 dimensions=(0.75*SCALE, 1*SCALE), density=1/SCALE,
                 position=(0, 0)):

        world = car.body.world

        self.initial_position = position 
        self.current_traction = 1
        # self.turn_torque = turn_torque
        self.max_forward_speed = max_forward_speed
        self.max_backward_speed = max_backward_speed
        self.max_drive_force = max_drive_force
        self.max_lateral_impulse = max_lateral_impulse
        # self.ground_areas = []

        self.body = world.CreateDynamicBody(position=position)
        self.body.CreatePolygonFixture(box=dimensions, density=density)
        self.body.userData = {'obj': self}

        # print(self.body)

        self.disabled = False

    @property
    def forward_velocity(self):
        body = self.body
        current_normal = body.GetWorldVector((0, 1))
        return current_normal.dot(body.linearVelocity) * current_normal

    @property
    def lateral_velocity(self):
        body = self.body

        right_normal = body.GetWorldVector((1, 0))
        return right_normal.dot(body.linearVelocity) * right_normal

    def update_friction(self):
        impulse = 0.4 * -self.lateral_velocity * self.body.mass
        if impulse.length > self.max_lateral_impulse:
            impulse *= self.max_lateral_impulse / impulse.length

        # Aplica impulso lineal en la direccion contraria a la velocidad lateral de la rueda
        self.body.ApplyLinearImpulse(self.current_traction * impulse, self.body.worldCenter, True)

        # Aplica impulso angular en la direccion contraria a la velocidad angular de la rueda
        aimp = 0.7 * self.current_traction * self.body.inertia * -self.body.angularVelocity
        self.body.ApplyAngularImpulse(aimp, True)

        current_forward_normal = self.forward_velocity
        current_forward_speed = current_forward_normal.Normalize()

        # Aplica fuerza en la direccion contraria a la direccion frontal de la velocidad
        drag_force_magnitude = -1.7 * current_forward_speed 
        self.body.ApplyForce(self.current_traction * drag_force_magnitude * current_forward_normal, self.body.worldCenter, True)

    def update_drive(self, keys):
        # find the current speed in the forward direction
        current_forward_normal = self.body.GetWorldVector((0, 1))
        current_speed = self.forward_velocity.dot(current_forward_normal)

        if 'up' in keys:
            desired_speed = self.max_forward_speed
        elif 'down' in keys:
            desired_speed = self.max_backward_speed
        else:            
            desired_speed = current_speed
        
        # apply necessary force
        force = 0.0
        if desired_speed > current_speed:
            force = self.max_drive_force
        elif desired_speed < current_speed:
            force = -self.max_drive_force
        else:
            return

        if not self.disabled:
            self.body.ApplyForce(self.current_traction * force * current_forward_normal,
                                self.body.worldCenter, True)

    # def update_turn(self, keys):
    #     if 'left' in keys:
    #         desired_torque = self.turn_torque
    #     elif 'right' in keys:
    #         desired_torque = -self.turn_torque
    #     else:
    #         return

    #     self.body.ApplyTorque(desired_torque, True)

    # def add_ground_area(self, ud):
    #     if ud not in self.ground_areas:
    #         self.ground_areas.append(ud)
    #         self.update_traction()

    # def remove_ground_area(self, ud):
    #     if ud in self.ground_areas:
    #         self.ground_areas.remove(ud)
    #         self.update_traction()

    # def update_traction(self):
    #     if not self.ground_areas:
    #         self.current_traction = 1
    #     else:
    #         self.current_traction = 0
    #         mods = [ga.friction_modifier for ga in self.ground_areas]

    #         max_mod = max(mods)
    #         if max_mod > self.current_traction:
    #             self.current_traction = max_mod


class TDCar(object):
    vertices = [(0, 6),
                (-3.5, 4),
                (-3.5, -6),
                (3.5, -6),
                (3.5, 4)
                ]

    tire_anchors = [(-3, -4),
                    (3, -4),
                    (-3, 3),
                    (3, 3)
                    ]

    # vertices = [(1.5, 0.0),
    #             (3.0, 2.5),
    #             (2.8, 5.5),
    #             (1.0, 10.0),
    #             (-1.0, 10.0),
    #             (-2.8, 5.5),
    #             (-3.0, 2.5),
    #             (-1.5, 0.0),
    #             ]

    # tire_anchors = [(-3.0, 0.75),
    #                 (3.0, 0.75),
    #                 (-3.0, 8.50),
    #                 (3.0, 8.50),
    #                 ]

    def __init__(self, world, vertices=None,
                 tire_anchors=None, density=0.1, position=(0, 0),
                 **tire_kws):

        TDCar.vertices = [(v[0]*SCALE, v[1]*SCALE) for v in TDCar.vertices]
        TDCar.tire_anchors = [(v[0]*SCALE, v[1]*SCALE) for v in TDCar.tire_anchors]

        if vertices is None:
            vertices = TDCar.vertices

        self.body = world.CreateDynamicBody(position=position)
        self.body.CreatePolygonFixture(vertices=vertices, density=density)
        self.body.userData = {'obj': self}

        self.tires = [TDTire(self, **tire_kws) for i in range(4)]

        self.tires[0].disabled = True
        self.tires[1].disabled = True

        self.tires[0].max_lateral_impulse = 2
        self.tires[1].max_lateral_impulse = 2

        # for i in range(4):
        #     mass = self.tires[i].body.mass
        #     inertia = self.tires[i].body.inertia
        #     world.DestroyBody(self.tires[i].body)
        #     self.tires[i].body = world.CreateDynamicBody(position=self.tires[0].initial_position)
        #     self.tires[i].body.mass = mass
        #     self.tires[i].body.inertia = inertia

        if tire_anchors is None:
            anchors = TDCar.tire_anchors

        joints = self.joints = []
        for tire, anchor in zip(self.tires, anchors):
            j = world.CreateRevoluteJoint(bodyA=self.body,
                                          bodyB=tire.body,
                                          localAnchorA=anchor,
                                          # center of tire
                                          localAnchorB=(0, 0),
                                          enableMotor=False,
                                          maxMotorTorque=1000,
                                          enableLimit=True,
                                          lowerAngle=0,
                                          upperAngle=0,
                                          )

            tire.body.position = self.body.worldCenter + anchor
            joints.append(j)

    def update(self, keys, hz):
        for tire in self.tires:
            tire.update_friction()

        for tire in self.tires:
            tire.update_drive(keys)

        # control steering
        lock_angle = math.radians(40.)
        # from lock to lock in 0.5 sec
        turn_speed_per_sec = math.radians(1600.)
        turn_per_timestep = turn_speed_per_sec / hz
        desired_angle = 0.0

        if 'left' in keys:
            desired_angle = lock_angle
        elif 'right' in keys:
            desired_angle = -lock_angle

        # Calcula self.steering_angle
        # [
        
        d = self.mouse_pos - self.body.position
        control_direction = Vector2(d.x, d.y)
        control_direction_normalized = control_direction.normalize()

        angle = (2 * math.pi) - (self.body.angle % (2 * math.pi))
        # print(angle) # angle esta entre [0, 2*pi]

        u = control_direction_normalized.rotate(degrees(angle)) 
        u = Vector2(u.y, u.x) # Rota u 90º CCW
        self.steering_angle = math.atan2(u.y, u.x) # El angulo esta entre [-pi, pi], los positivos son CW
        print(self.steering_angle)
        
        # ]

        desired_angle = -self.steering_angle

        MAX_ANGLE = math.pi / 4
        desired_angle = max(min(desired_angle, MAX_ANGLE), -MAX_ANGLE)

        front_left_joint, front_right_joint = self.joints[2:4]
        angle_now = front_left_joint.angle
        angle_to_turn = desired_angle - angle_now

        # TODO fix b2Clamp for non-b2Vec2 types
        # if angle_to_turn < -turn_per_timestep:
        #     angle_to_turn = -turn_per_timestep
        # elif angle_to_turn > turn_per_timestep:
        #     angle_to_turn = turn_per_timestep

        new_angle = angle_now + angle_to_turn
        # Rotate the tires by locking the limits:
        front_left_joint.SetLimits(new_angle, new_angle)
        front_right_joint.SetLimits(new_angle, new_angle)

        # print(new_angle)

class TopDownCar (Framework):
    name = "Top Down Car"
    description = "Keys: accel = UP, reverse = DOWN, left = LEFT, right = RIGHT"

    def __init__(self):
        super(TopDownCar, self).__init__()
        # Top-down -- no gravity in the screen plane
        self.world.gravity = (0, 0)

        self.settings.hz = 30
        self.settings.velocityIterations = 2
        self.settings.positionIterations = 1
        # Makes physics results more accurate (see Box2D wiki)
        enableWarmStarting = True
        enableContinuous = False     # Calculate time of impact

        self.settings.drawMenu = False
        self.settings.drawStats = False

        self.key_map = {Keys.K_UP: 'up',
                        Keys.K_DOWN: 'down',
                        Keys.K_LEFT: 'left',
                        Keys.K_RIGHT: 'right',
                        }

        # Keep track of the pressed keys
        self.pressed_keys = set()

        self.mouse_pos = Vector2()

        # The walls
        # boundary = self.world.CreateStaticBody(position=(0, 20))
        # boundary.CreateEdgeChain([(-30, -30),
        #                           (-30, 30),
        #                           (30, 30),
        #                           (30, -30),
        #                           (-30, -30)]
        #                          )

        # A couple regions of differing traction
        self.car = TDCar(self.world)

    def _mouse_move(self, sp, wp): # screen pos, world pos
        self.car.mouse_pos = wp

    def MouseDown(self, p):
        super().MouseDown(p)
        self.pressed_keys.add('up')

    def MouseUp(self, p):
        super().MouseUp(p)
        if 'up' in self.pressed_keys:
            self.pressed_keys.remove('up')

    def Keyboard(self, key):
        key_map = self.key_map
        if key in key_map:
            self.pressed_keys.add(key_map[key])
        else:
            super(TopDownCar, self).Keyboard(key)

    def KeyboardUp(self, key):
        key_map = self.key_map
        if key in key_map:
            self.pressed_keys.remove(key_map[key])
        else:
            super(TopDownCar, self).KeyboardUp(key)

    def handle_contact(self, contact, began):
        # A contact happened -- see if a wheel hit a
        # ground area
        fixture_a = contact.fixtureA
        fixture_b = contact.fixtureB

        body_a, body_b = fixture_a.body, fixture_b.body
        ud_a, ud_b = body_a.userData, body_b.userData
        if not ud_a or not ud_b:
            return

        tire = None
        for ud in (ud_a, ud_b):
            obj = ud['obj']
            if isinstance(obj, TDTire):
                tire = obj

    def BeginContact(self, contact):
        self.handle_contact(contact, True)

    def EndContact(self, contact):
        self.handle_contact(contact, False)

    def Step(self, settings):
        self.car.update(self.pressed_keys, settings.hz)

        super(TopDownCar, self).Step(settings)

        tractions = [tire.current_traction for tire in self.car.tires]
        # self.Print('Current tractions: %s' % tractions)
        
        self.Print('Position: %s' % self.car.body.position)
        

if __name__ == "__main__":
    main(TopDownCar)