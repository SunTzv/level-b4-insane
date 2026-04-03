import pygame
import math
import os
import random
from settings import *
from utils.geometry import get_diamond_footprint
from entities.level import tile_center, PARKING_PATHS, grid_to_screen

ASSETS_DIR = "assets"

def _load_car_img(filename, size):
    path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size)
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill((100, 100, 100))
    return surf

# ---------------------------------------------------------------------------
# Player-drivable car
# ---------------------------------------------------------------------------
class Car(pygame.sprite.Sprite):
    def __init__(self, x, y, plate):
        super().__init__()
        self.original_image = _load_car_img("generic_car.png", (48, 24))
        self.image  = self.original_image
        self.rect   = self.image.get_rect(center=(x, y))
        self.hitbox = get_diamond_footprint(self.rect)
        self.plate       = plate
        self.angle       = 0.0
        self.speed       = 0.0
        self.max_speed   = 250
        self.acceleration = 150
        self.friction    = 80
        self.turn_speed  = 120
        self.is_driven   = False
        self.doors_locked = False

    def update(self, dt):
        if self.is_driven:
            keys = pygame.key.get_pressed()
            if   keys[pygame.K_w] or keys[pygame.K_UP]:    self.speed += self.acceleration * dt
            elif keys[pygame.K_s] or keys[pygame.K_DOWN]:  self.speed -= self.acceleration * dt
            else: self._friction(dt)
            self.speed = max(-self.max_speed/2, min(self.speed, self.max_speed))
            if self.speed != 0:
                d = 1 if self.speed > 0 else -1
                if keys[pygame.K_a] or keys[pygame.K_LEFT]:  self.angle -= self.turn_speed * dt * d
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.angle += self.turn_speed * dt * d
        else:
            self._friction(dt)
        rad = math.radians(self.angle)
        self.rect.x += math.cos(rad) * self.speed * dt
        self.rect.y += math.sin(rad) * self.speed * dt
        c = self.rect.center
        self.image = pygame.transform.rotate(self.original_image, -self.angle)
        self.rect  = self.image.get_rect(center=c)
        self.hitbox = get_diamond_footprint(self.rect)

    def _friction(self, dt):
        if   self.speed > 0: self.speed = max(0.0, self.speed - self.friction * dt)
        elif self.speed < 0: self.speed = min(0.0, self.speed + self.friction * dt)


# ---------------------------------------------------------------------------
# NPC Car — waits at barrier, follows waypoints to parking spot
# ---------------------------------------------------------------------------
CREEPY_LINES = [
    "YOU LOGGED 10 CARS.\nTHERE ARE 11 IN THE LOT.",
    "I HAVE BEEN HERE BEFORE.\nSO HAVE YOU.",
    "DON'T OPEN THE DOOR.\nYOU WON'T LIKE WHAT'S INSIDE.",
    "THE SHIFT ENDS.\nDOES IT, THOUGH?",
    "THIS PLATE WAS NEVER REGISTERED.\nIT NEVER WAS.",
    "CHECK THE LOG AGAIN.\nCOUNT THEM.",
]

class NPCCar(pygame.sprite.Sprite):
    WAIT     = 'waiting'      # sitting outside the barrier
    ENTERING = 'entering'     # moving to first waypoint (inside barrier)
    DRIVING  = 'driving'      # following remaining waypoints
    PARKED   = 'parked'
    NPC_SPEED = 65

    def __init__(self, entry_pos, path_grids, plate, is_anomaly=False, spot_idx=0):
        super().__init__()
        self.original_image = _load_car_img("generic_car.png", (48, 24))
        self.image  = self.original_image
        self.rect   = self.image.get_rect(center=(int(entry_pos.x), int(entry_pos.y)))
        self.hitbox = get_diamond_footprint(self.rect)
        self.plate       = plate
        self.is_anomaly  = is_anomaly
        self.doors_locked = True
        self.is_driven   = False
        self.logged      = False
        self.state       = self.WAIT
        self._angle      = 90.0

        # Convert grid path to world waypoints
        self.waypoints = [tile_center(c, r) for c, r in path_grids]
        self._wp = 0

    def allow_enter(self):
        """Called by Game when player opens the barrier."""
        if self.state == self.WAIT:
            self.state = self.ENTERING

    def update(self, dt):
        if self.state in (self.WAIT, self.PARKED):
            return
        if self._wp >= len(self.waypoints):
            self.state = self.PARKED
            return
        self._move_toward(self.waypoints[self._wp], dt)

    def _move_toward(self, target, dt):
        direction = target - pygame.math.Vector2(self.rect.center)
        if direction.length() < 6:
            self._wp += 1
            if self._wp >= len(self.waypoints):
                self.state = self.PARKED
            elif self.state == self.ENTERING:
                self.state = self.DRIVING
            return
        direction = direction.normalize()
        self.rect.x += direction.x * self.NPC_SPEED * dt
        self.rect.y += direction.y * self.NPC_SPEED * dt
        self._angle = math.degrees(math.atan2(direction.y, direction.x))
        c = self.rect.center
        self.image = pygame.transform.rotate(self.original_image, -self._angle)
        self.rect  = self.image.get_rect(center=c)
        self.hitbox = get_diamond_footprint(self.rect)

    def creepy_message(self):
        return random.choice(CREEPY_LINES)


# ---------------------------------------------------------------------------
# Autonomous black sedan (Day 2+)
# ---------------------------------------------------------------------------
class AutonomousCar(Car):
    def __init__(self, x, y, plate, player):
        super().__init__(x, y, plate)
        self.original_image = _load_car_img("car_black_sedan.png", (48, 24))
        self.image  = self.original_image
        self.rect   = self.image.get_rect(center=(x, y))
        self.player = player
        self.creep_speed  = 25
        self.doors_locked = True

    def update(self, dt):
        super().update(dt)
        if self.is_driven: return
        dist = pygame.math.Vector2(self.rect.center).distance_to(self.player.rect.center)
        if dist > 260:
            d = (pygame.math.Vector2(self.player.rect.center)
                 - pygame.math.Vector2(self.rect.center)).normalize()
            self.rect.x += d.x * self.creep_speed * dt
            self.rect.y += d.y * self.creep_speed * dt
            self.hitbox  = get_diamond_footprint(self.rect)
