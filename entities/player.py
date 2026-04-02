import pygame
from settings import *
from utils.geometry import get_diamond_footprint
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((32, 64))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 200
        self.hitbox = get_diamond_footprint(self.rect)
        self.in_car = False
        self.current_car = None

    def update(self, dt):
        if self.in_car and self.current_car:
            self.rect.center = self.current_car.rect.center
            self.hitbox = get_diamond_footprint(self.rect)
            return

        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        
        # Normalize to prevent faster diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
            
        self.rect.x += dx * self.speed * dt
        self.rect.y += dy * self.speed * dt
        
        # Update hitbox based on new rect
        self.hitbox = get_diamond_footprint(self.rect)
