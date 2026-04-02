import pygame
from settings import *

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.half_w = self.display_surface.get_size()[0] // 2
        self.half_h = self.display_surface.get_size()[1] // 2
        self.offset = pygame.math.Vector2()

    def custom_draw(self, player):
        # Center the camera on the player
        self.offset.x = player.rect.centerx - self.half_w
        self.offset.y = player.rect.centery - self.half_h

        # Y-Sort elements by their rect.bottom coordinate
        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.bottom):
            if hasattr(sprite, 'in_car') and sprite.in_car:
                continue
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)
