import pygame
import os
from settings import *

# Grid-to-screen conversion for isometric tiles
# Formula: each grid cell (col, row) maps to screen pixel (x, y) using:
#   x = (col - row) * TILE_W // 2
#   y = (col + row) * TILE_H // 2
# This creates the classic isometric diamond grid.

def grid_to_screen(col, row):
    x = (col - row) * TILE_W // 2
    y = (col + row) * TILE_H // 2
    return x, y

class TileMap:
    TILE_IMAGES = {
        'C': os.path.join('assets', 'floor_concrete.png'),  # C = Concrete
    }

    # Map layout — each character is one tile on the grid.
    # '.' = empty/no tile, 'C' = floor_concrete
    LAYOUT = [
        "CCCCCCCCCCCCCCCCCCCC",
        "CCCCCCCCCCCCCCCCCCCC",
        "CCCCCCCCCCCCCCCCCCCC",
        "CCCCCCCCCCCCCCCCCCCC",
        "CCCCCCCCCCCCCCCCCCCC",
        "CCCCCCCCCCCCCCCCCCCC",
        "CCCCCCCCCCCCCCCCCCCC",
        "CCCCCCCCCCCCCCCCCCCC",
        "CCCCCCCCCCCCCCCCCCCC",
        "CCCCCCCCCCCCCCCCCCCC",
        "CCCCCCCCCCCCCCCCCCCC",
        "CCCCCCCCCCCCCCCCCCCC",
    ]

    def __init__(self):
        self._load_images()
        self.tiles = self._build_tiles()

    def _load_images(self):
        self.images = {}
        for key, path in self.TILE_IMAGES.items():
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (TILE_W, TILE_H))
                self.images[key] = img
            else:
                # Fallback: plain dark grey diamond-shaped surface
                surf = pygame.Surface((TILE_W, TILE_H), pygame.SRCALPHA)
                pygame.draw.polygon(surf, DARK_GREY, [
                    (TILE_W // 2, 0),
                    (TILE_W, TILE_H // 2),
                    (TILE_W // 2, TILE_H),
                    (0, TILE_H // 2),
                ])
                self.images[key] = surf

    def _build_tiles(self):
        """Pre-compute (image, screen_pos) for every tile in the layout."""
        tiles = []
        for row_idx, row_str in enumerate(self.LAYOUT):
            for col_idx, char in enumerate(row_str):
                if char == '.':
                    continue
                img = self.images.get(char)
                if img is None:
                    continue
                sx, sy = grid_to_screen(col_idx, row_idx)
                # Anchor at top-left of the tile rect
                tiles.append((img, pygame.math.Vector2(sx, sy)))
        return tiles

    def draw(self, surface, camera_offset):
        """Draw all floor tiles, shifted by the camera offset."""
        for img, world_pos in self.tiles:
            screen_pos = world_pos - camera_offset
            surface.blit(img, screen_pos)
