import pygame
from settings import *

class LightingManager:
    def __init__(self, width, height):
        self.darkness = pygame.Surface((width, height), pygame.SRCALPHA)
        self.light_cache = {}
        
    def get_light_mask(self, radius, intensity=255):
        if (radius, intensity) in self.light_cache:
            return self.light_cache[(radius, intensity)]
            
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r in range(radius, 0, -1):
            alpha = int(intensity * (1 - r / radius))
            # Subtract color logic: RGB doesn't matter much for SUB, we just need alpha
            pygame.draw.circle(surf, (255, 255, 255, alpha), (radius, radius), r)
            
        self.light_cache[(radius, intensity)] = surf
        return surf
        
    def draw(self, screen, offset, lights, state_manager):
        opacity = 180
        if state_manager.state.name == "DECAY":
            opacity = 220
        elif state_manager.state.name == "NIGHTMARE":
            opacity = 250
            
        self.darkness.fill((0, 0, 0, opacity))
        
        for light in lights:
            pos = light['pos'] - offset
            radius = light['radius']
            mask = self.get_light_mask(radius)
            
            # Using BLEND_RGBA_SUB to cut out the darkness
            self.darkness.blit(mask, (pos.x - radius, pos.y - radius), special_flags=pygame.BLEND_RGBA_SUB)
            
        screen.blit(self.darkness, (0, 0))
