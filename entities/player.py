import pygame
import os
from settings import *
from utils.geometry import get_diamond_footprint

class Player(pygame.sprite.Sprite):
    ASSET_PATH = os.path.join("assets", "player.png")

    def __init__(self, x, y):
        super().__init__()
        if os.path.exists(self.ASSET_PATH):
            self.original_image = pygame.image.load(self.ASSET_PATH).convert_alpha()
            self.original_image = pygame.transform.scale(self.original_image, (20, 36))
        else:
            self.original_image = pygame.Surface((20, 36), pygame.SRCALPHA)
            self.original_image.fill(WHITE)
        self.image  = self.original_image
        self.rect   = self.image.get_rect(center=(x, y))
        self.speed  = 120
        self.hitbox = get_diamond_footprint(self.rect)
        self.in_car        = False
        self.current_car   = None
        self.flashlight_on = False
        self._tilemap      = None

    def set_tilemap(self, tilemap):
        self._tilemap = tilemap

    # -----------------------------------------------------------------------
    def update(self, dt):
        if self.in_car and self.current_car:
            self.rect.center = self.current_car.rect.center
            self.hitbox = get_diamond_footprint(self.rect)
            return

        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1

        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071

        step = self.speed * dt

        # Slide along each axis independently for smooth wall-sliding
        new_x = self.rect.x + dx * step
        if not self._blocked(new_x, self.rect.y):
            self.rect.x = new_x

        new_y = self.rect.y + dy * step
        if not self._blocked(self.rect.x, new_y):
            self.rect.y = new_y

        self.hitbox = get_diamond_footprint(self.rect)

    def _blocked(self, rx, ry):
        if self._tilemap is None:
            return False
        # Use the player's ground centre — slightly above the very bottom
        # to match the isometric "standing plane"
        fx = rx + self.rect.width  // 2
        fy = ry + self.rect.height - 8
        return self._tilemap.is_solid_at(fx, fy)
