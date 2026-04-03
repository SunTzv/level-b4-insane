import pygame
import os
from settings import *
from utils.geometry import get_diamond_footprint

class Player(pygame.sprite.Sprite):
    ASSET_PATH = os.path.join("assets", "player.png")
    # Foot rect size relative to sprite (used for collision checks)
    FOOT_W = 14
    FOOT_H = 10

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
        self.in_car       = False
        self.current_car  = None
        self.flashlight_on = False
        self._collision_rects = []   # set by Game via set_tilemap()

    def set_tilemap(self, tilemap):
        self._collision_rects = tilemap.collision_rects

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

        # Slide along X, then Y separately so corners feel smooth
        new_x = self.rect.x + dx * step
        if not self._collides(new_x, self.rect.y):
            self.rect.x = new_x

        new_y = self.rect.y + dy * step
        if not self._collides(self.rect.x, new_y):
            self.rect.y = new_y

        self.hitbox = get_diamond_footprint(self.rect)

    def _foot_rect(self, rx, ry):
        """A small rect at the bottom-centre of the sprite — the "ground" point."""
        cx = rx + self.rect.width  // 2
        cy = ry + self.rect.height - self.FOOT_H
        return pygame.Rect(cx - self.FOOT_W // 2, cy,
                           self.FOOT_W, self.FOOT_H)

    def _collides(self, rx, ry):
        """Return True if the foot rect overlaps any solid tile rect."""
        foot = self._foot_rect(rx, ry)
        return any(foot.colliderect(r) for r in self._collision_rects)
