import pygame
import math
from settings import *
from utils.geometry import get_diamond_footprint

class Car(pygame.sprite.Sprite):
    def __init__(self, x, y, plate):
        super().__init__()
        self.image = pygame.Surface((64, 32))
        self.image.fill((100, 100, 100)) # Gray
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = get_diamond_footprint(self.rect)
        
        self.plate = plate
        self.angle = 0
        self.speed = 0
        self.max_speed = 300
        self.acceleration = 150
        self.friction = 75
        self.turn_speed = 120
        self.is_driven = False

    def update(self, dt):
        if self.is_driven:
            keys = pygame.key.get_pressed()
            
            # Acceleration
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                self.speed += self.acceleration * dt
            elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                self.speed -= self.acceleration * dt
            else:
                self._apply_friction(dt)
            
            # Cap speed
            if self.speed > self.max_speed:
                self.speed = self.max_speed
            elif self.speed < -self.max_speed / 2: # Slower in reverse
                self.speed = -self.max_speed / 2
                
            # Turning
            if self.speed != 0:
                turn_dir = 1 if self.speed > 0 else -1
                if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    self.angle -= self.turn_speed * dt * turn_dir
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    self.angle += self.turn_speed * dt * turn_dir
                    
        else:
            self._apply_friction(dt)
            
        # Move based on angle and speed
        rad = math.radians(self.angle)
        dx = math.cos(rad) * self.speed * dt
        dy = math.sin(rad) * self.speed * dt
        
        self.rect.x += dx
        self.rect.y += dy
        self.hitbox = get_diamond_footprint(self.rect)

    def _apply_friction(self, dt):
        if self.speed > 0:
            self.speed -= self.friction * dt
            self.speed = max(0, self.speed)
        elif self.speed < 0:
            self.speed += self.friction * dt
            self.speed = min(0, self.speed)

class AutonomousCar(Car):
    def __init__(self, x, y, plate, player):
        super().__init__(x, y, plate)
        self.image.fill((10, 10, 15)) # Deep black tint
        self.player = player
        self.creep_speed = 30
        self.doors_locked = True
        
    def update(self, dt):
        super().update(dt)
        
        if self.is_driven: 
            return
            
        dist = pygame.math.Vector2(self.rect.center).distance_to(self.player.rect.center)
        # Move only when player is far away (simulating player's back turned / not looking closely)
        if dist > 250:
            direction = pygame.math.Vector2(self.player.rect.center) - pygame.math.Vector2(self.rect.center)
            if direction.length() > 0:
                direction = direction.normalize()
                
            self.rect.x += direction.x * self.creep_speed * dt
            self.rect.y += direction.y * self.creep_speed * dt
            self.hitbox = get_diamond_footprint(self.rect)
