import pygame
import math
import os
import random
from settings import *
from utils.geometry import get_diamond_footprint

ASSETS_DIR = "assets"

# ---------------------------------------------------------------------------
# Base Car (player-drivable, tank controls)
# ---------------------------------------------------------------------------
class Car(pygame.sprite.Sprite):
    def __init__(self, x, y, plate):
        super().__init__()
        asset = os.path.join(ASSETS_DIR, "generic_car.png")
        if os.path.exists(asset):
            self.original_image = pygame.image.load(asset).convert_alpha()
            self.original_image = pygame.transform.scale(self.original_image, (48, 24))
        else:
            self.original_image = pygame.Surface((48, 24))
            self.original_image.fill((100, 100, 100))
        self.image = self.original_image
        self.rect  = self.image.get_rect(center=(x, y))
        self.hitbox = get_diamond_footprint(self.rect)

        self.plate       = plate
        self.angle       = 0
        self.speed       = 0
        self.max_speed   = 250
        self.acceleration = 150
        self.friction    = 80
        self.turn_speed  = 120
        self.is_driven   = False

    def update(self, dt):
        if self.is_driven:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.speed += self.acceleration * dt
            elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.speed -= self.acceleration * dt
            else:
                self._apply_friction(dt)

            self.speed = max(-self.max_speed / 2, min(self.speed, self.max_speed))

            if self.speed != 0:
                turn_dir = 1 if self.speed > 0 else -1
                keys = pygame.key.get_pressed()
                if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    self.angle -= self.turn_speed * dt * turn_dir
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    self.angle += self.turn_speed * dt * turn_dir
        else:
            self._apply_friction(dt)

        rad = math.radians(self.angle)
        self.rect.x += math.cos(rad) * self.speed * dt
        self.rect.y += math.sin(rad) * self.speed * dt

        center = self.rect.center
        self.image = pygame.transform.rotate(self.original_image, -self.angle)
        self.rect  = self.image.get_rect(center=center)
        self.hitbox = get_diamond_footprint(self.rect)

    def _apply_friction(self, dt):
        if self.speed > 0:
            self.speed = max(0, self.speed - self.friction * dt)
        elif self.speed < 0:
            self.speed = min(0, self.speed + self.friction * dt)


# ---------------------------------------------------------------------------
# NPC Car — follows waypoints automatically, parks itself
# ---------------------------------------------------------------------------
CREEPY_LINES = [
    "YOU LOGGED 10 CARS.\nTHERE ARE 11 IN THE LOT.",
    "I'VE BEEN HERE BEFORE.\nSO HAVE YOU.",
    "DON'T OPEN THE DOOR.\nYOU WON'T LIKE WHAT'S INSIDE.",
    "SHIFT ENDS.\nDOES IT?",
    "THE PLATE IS NOT REGISTERED.\nIT NEVER WAS.",
]

class NPCCar(pygame.sprite.Sprite):
    STATE_ENTERING  = 'entering'
    STATE_PARKING   = 'parking'
    STATE_PARKED    = 'parked'
    STATE_CREEPY    = 'creepy'   # anomaly car — shift over

    NPC_SPEED = 70

    def __init__(self, entry_pos, lane_pos, park_pos, plate, is_anomaly=False):
        super().__init__()
        asset = os.path.join(ASSETS_DIR, "generic_car.png")
        if os.path.exists(asset):
            self.original_image = pygame.image.load(asset).convert_alpha()
            self.original_image = pygame.transform.scale(self.original_image, (48, 24))
        else:
            self.original_image = pygame.Surface((48, 24))
            self.original_image.fill((120, 120, 120))
        self.image  = self.original_image
        self.rect   = self.image.get_rect(center=(int(entry_pos.x), int(entry_pos.y)))
        self.hitbox = get_diamond_footprint(self.rect)

        self.plate       = plate
        self.is_anomaly  = is_anomaly
        self.doors_locked = True        # NPC cars can't be entered by player
        self.is_driven   = False
        self.logged      = False        # True once player logs this plate

        # Waypoints: entry → lane → park
        self.waypoints = [lane_pos, pygame.math.Vector2(park_pos[0] + TILE_W//2,
                                                         park_pos[1] + TILE_H//2)]
        self.wp_idx  = 0
        self.state   = self.STATE_ENTERING
        self._angle  = 180.0             # start pointing "into" the lot

    def update(self, dt):
        if self.state == self.STATE_PARKED or self.state == self.STATE_CREEPY:
            return

        if self.wp_idx >= len(self.waypoints):
            self.state = self.STATE_PARKED if not self.is_anomaly else self.STATE_PARKED
            return

        target = self.waypoints[self.wp_idx]
        direction = target - pygame.math.Vector2(self.rect.center)
        if direction.length() < 8:
            self.wp_idx += 1
            if self.wp_idx >= len(self.waypoints):
                self.state = self.STATE_PARKED
            return

        direction = direction.normalize()
        self.rect.x += direction.x * self.NPC_SPEED * dt
        self.rect.y += direction.y * self.NPC_SPEED * dt

        self._angle = math.degrees(math.atan2(direction.y, direction.x))
        center = self.rect.center
        self.image = pygame.transform.rotate(self.original_image, -self._angle)
        self.rect  = self.image.get_rect(center=center)
        self.hitbox = get_diamond_footprint(self.rect)

    def get_creepy_message(self):
        return random.choice(CREEPY_LINES)


# ---------------------------------------------------------------------------
# Autonomous black sedan (Day 2+)
# ---------------------------------------------------------------------------
class AutonomousCar(Car):
    def __init__(self, x, y, plate, player):
        super().__init__(x, y, plate)
        asset = os.path.join(ASSETS_DIR, "car_black_sedan.png")
        if os.path.exists(asset):
            self.original_image = pygame.image.load(asset).convert_alpha()
            self.original_image = pygame.transform.scale(self.original_image, (48, 24))
        else:
            self.original_image = pygame.Surface((48, 24), pygame.SRCALPHA)
            self.original_image.fill((10, 10, 15))
        self.image  = self.original_image
        self.rect   = self.image.get_rect(center=(x, y))
        self.player = player
        self.creep_speed  = 25
        self.doors_locked = True

    def update(self, dt):
        super().update(dt)
        if self.is_driven:
            return
        dist = pygame.math.Vector2(self.rect.center).distance_to(self.player.rect.center)
        if dist > 260:
            direction = (pygame.math.Vector2(self.player.rect.center)
                         - pygame.math.Vector2(self.rect.center))
            if direction.length() > 0:
                direction = direction.normalize()
            self.rect.x += direction.x * self.creep_speed * dt
            self.rect.y += direction.y * self.creep_speed * dt
            self.hitbox  = get_diamond_footprint(self.rect)
