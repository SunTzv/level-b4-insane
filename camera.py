import pygame
from settings import *

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.half_w = RENDER_W // 2
        self.half_h = RENDER_H // 2
        self.offset = pygame.math.Vector2()

    def update_offset(self, target):
        self.offset.x = target.rect.centerx - self.half_w
        self.offset.y = target.rect.centery - self.half_h

    def custom_draw(self, target, surface):
        """Draw all sprites into 'surface' (the small render surface)."""
        self.update_offset(target)
        for sprite in sorted(self.sprites(), key=lambda s: s.rect.bottom):
            if hasattr(sprite, 'in_car') and sprite.in_car:
                continue
            screen_pos = pygame.math.Vector2(sprite.rect.topleft) - self.offset
            surface.blit(sprite.image, screen_pos)
