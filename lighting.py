import pygame
from settings import *

class LightingManager:
    # Darkness opacity per game state (0 = fully bright, 255 = pitch black)
    OPACITY = {
        'NORMAL':    80,   # Day 1-2: dim but playable — overhead fluorescents
        'DECAY':    160,   # Day 3-4: noticeably darker, shadows stretch
        'NIGHTMARE': 210,  # Day 5:   near-total darkness
    }

    def __init__(self, width, height):
        self.darkness = pygame.Surface((width, height), pygame.SRCALPHA)
        self.light_cache = {}

    def _get_light_mask(self, radius):
        """Return a cached circular gradient surface for a given radius."""
        if radius in self.light_cache:
            return self.light_cache[radius]

        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r in range(radius, 0, -1):
            # Smooth quadratic falloff — bright in center, fades at edge
            t = r / radius
            alpha = int(255 * (t * t))
            pygame.draw.circle(surf, (255, 255, 255, alpha), (radius, radius), r)

        self.light_cache[radius] = surf
        return surf

    def draw(self, screen, offset, lights, state_manager):
        opacity = self.OPACITY.get(state_manager.state.name, 80)
        self.darkness.fill((0, 0, 0, opacity))

        for light in lights:
            pos = light['pos'] - offset
            radius = light['radius']
            mask = self._get_light_mask(radius)
            self.darkness.blit(
                mask,
                (pos.x - radius, pos.y - radius),
                special_flags=pygame.BLEND_RGBA_SUB
            )

        screen.blit(self.darkness, (0, 0))
