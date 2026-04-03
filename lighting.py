import pygame
from settings import *

class LightingManager:
    """
    Fast lighting using BLEND_MULT instead of SRCALPHA surfaces.

    How it works:
      1. Fill darkness surface with an ambient RGB colour (not alpha — regular surface).
      2. Blit pre-rendered white-to-black radial gradients onto it with BLEND_ADD
         (adds brightness where lights are).
      3. Blit the darkness surface onto the screen with BLEND_MULT.
         BLEND_MULT: result = screen_pixel * darkness_pixel / 255
         → black (0)   in darkness = screen goes black
         → white (255) in darkness = screen pixel unchanged
         → grey  (160) in darkness = screen dimmed by ~37%

    Why this is fast:
      • No SRCALPHA surface — fill() is ~10x faster on regular surfaces.
      • BLEND_MULT / BLEND_ADD are implemented in C inside SDL.
      • Light mask generated once and cached — never re-drawn.
      • Circle step=4 during mask generation (still smooth, 4x faster to build).
    """

    # RGB brightness of the ambient darkness layer per game state.
    # Higher = brighter (less dark).
    AMBIENT = {
        'NORMAL':    (155, 155, 155),
        'DECAY':     (70,  70,  70),
        'NIGHTMARE': (18,  18,  18),
    }

    def __init__(self, width=RENDER_W, height=RENDER_H):
        self.darkness = pygame.Surface((width, height))
        self.light_cache: dict = {}

    # ------------------------------------------------------------------
    def _get_light_mask(self, radius: int) -> pygame.Surface:
        """Return a cached radial gradient — white centre, black edge."""
        if radius in self.light_cache:
            return self.light_cache[radius]

        diam = radius * 2
        surf = pygame.Surface((diam, diam))
        surf.fill((0, 0, 0))

        # Draw rings from outside-in, each ring brighter than the last.
        # step=4 → ~4× faster than step=1, gradient still looks smooth.
        for r in range(radius, 0, -4):
            t = 1.0 - (r / radius)           # 0 at edge → 1 at centre
            b = int(255 * (t ** 1.4))        # power-curve falloff
            c = (b, b, b)
            pygame.draw.circle(surf, c, (radius, radius), r)

        self.light_cache[radius] = surf
        return surf

    # ------------------------------------------------------------------
    def draw(self, screen: pygame.Surface, offset: pygame.math.Vector2,
             lights: list, state_manager) -> None:

        ambient = self.AMBIENT.get(state_manager.state.name, self.AMBIENT['NORMAL'])
        self.darkness.fill(ambient)

        for light in lights:
            pos    = light['pos'] - offset
            radius = light['radius']
            mask   = self._get_light_mask(radius)
            # BLEND_ADD: adds the bright centre to the darkness layer
            self.darkness.blit(
                mask,
                (int(pos.x - radius), int(pos.y - radius)),
                special_flags=pygame.BLEND_ADD,
            )

        # BLEND_MULT: multiplies screen by darkness — black=off, white=pass-through
        screen.blit(self.darkness, (0, 0), special_flags=pygame.BLEND_MULT)
