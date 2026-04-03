import pygame
import os
from settings import *

# ---------------------------------------------------------------------------
# Grid-to-screen conversion for isometric tiles
# Each grid cell (col, row) maps to screen pixel (x, y):
#   x = (col - row) * TILE_W // 2
#   y = (col + row) * TILE_H // 2
# ---------------------------------------------------------------------------

def grid_to_screen(col, row):
    x = (col - row) * TILE_W // 2
    y = (col + row) * TILE_H // 2
    return x, y


# ---------------------------------------------------------------------------
# Tile definitions
# key  : single character used in LAYOUT string
# path : relative asset path
# size : (width, height) in pixels — must match the art
# z    : draw layer — 0 = floor (drawn first), 1 = wall/object (Y-sorted later)
# ---------------------------------------------------------------------------
TILE_DEFS = {
    # Floor tiles  (flat, 64×32 diamond)
    'C': {'path': os.path.join('assets', 'floor_concrete.png'),      'size': (64, 32), 'z': 0},
    'P': {'path': os.path.join('assets', 'tiles', 'floor_parking_line.png'), 'size': (64, 32), 'z': 0},

    # Tall / upright objects  (drawn after floor, Y-sorted with sprites)
    'W': {'path': os.path.join('assets', 'tiles', 'wall.png'),           'size': (64, 96), 'z': 1},
    'I': {'path': os.path.join('assets', 'tiles', 'pillar.png'),         'size': (32, 80), 'z': 1},
    'X': {'path': os.path.join('assets', 'tiles', 'barrier_closed.png'), 'size': (64, 48), 'z': 1},
    'O': {'path': os.path.join('assets', 'tiles', 'barrier_open.png'),   'size': (64, 48), 'z': 1},
    'E': {'path': os.path.join('assets', 'tiles', 'elevator_door.png'),  'size': (64, 80), 'z': 1},

    '.': None,  # empty cell — nothing drawn
}

# Fallback colours shown when the PNG file is missing
FALLBACK_COLORS = {
    'C': (60,  60,  60),   # dark concrete grey
    'P': (70,  70,  50),   # parking line — slightly greenish grey
    'W': (80,  80,  80),   # wall
    'I': (90,  90,  90),   # pillar — slightly lighter
    'X': (180, 40,  40),   # barrier closed — red
    'O': (40,  180, 40),   # barrier open   — green
    'E': (100, 100, 130),  # elevator door  — steel blue
}


def _make_fallback(key, w, h):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    color = FALLBACK_COLORS.get(key, (80, 80, 80))
    if h == 32:
        # Diamond for floor tiles
        pygame.draw.polygon(surf, color, [
            (w // 2, 0),
            (w, h // 2),
            (w // 2, h),
            (0, h // 2),
        ])
    else:
        # Solid rectangle for tall objects
        surf.fill((*color, 200))
    return surf


class TileMap:
    # ---------------------------------------------------------------------------
    # Edit LAYOUT to design the parking lot.
    # Each character maps to a key in TILE_DEFS.
    # The grid is 20 columns wide and 12 rows tall.
    # ---------------------------------------------------------------------------
    LAYOUT = [
        "WWWWWWWWWWWWWWWWWWWW",
        "WCCCCCCCCCCCCCCCCCCW",
        "WCCPPPPCCCCCPPPPCCEW",
        "WCCPPPPCCCCCPPPPCCEW",
        "WCCI...ICCCI...ICCW",
        "WCCCCCCCCCCCCCCCCCW",
        "WCCCCCCCCCCCCCCCCCW",
        "WCCCCCCCCCCCCCCCCCW",
        "WCCCCCCCCCCCCCCCCCW",
        "WCCPPPPCCCCCPPPPCCW",
        "WCCPPPPCCCCCPPPPCCW",
        "WWWWWWWWXWWWWWWWWWW",
    ]

    def __init__(self):
        self._load_images()

        # floor_tiles : drawn before sprites (z=0)
        # object_tiles: drawn with sprites in Y-sort order (z=1)
        self.floor_tiles = []
        self.object_tiles = []   # list of (img, world_pos_vec2, sort_y)
        self._build_tiles()

    # ------------------------------------------------------------------
    def _load_images(self):
        self.images = {}
        for key, defn in TILE_DEFS.items():
            if defn is None:
                continue
            w, h = defn['size']
            path = defn['path']
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (w, h))
            else:
                img = _make_fallback(key, w, h)
            self.images[key] = img

    def _build_tiles(self):
        for row_idx, row_str in enumerate(self.LAYOUT):
            for col_idx, char in enumerate(row_str):
                defn = TILE_DEFS.get(char)
                if defn is None:
                    continue
                img = self.images.get(char)
                if img is None:
                    continue

                sx, sy = grid_to_screen(col_idx, row_idx)
                pos = pygame.math.Vector2(sx, sy)
                w, h = defn['size']

                if defn['z'] == 0:
                    self.floor_tiles.append((img, pos))
                else:
                    # sort_y = bottom edge of the tile in world space
                    sort_y = sy + h
                    self.object_tiles.append((img, pos, sort_y))

        # Pre-sort object tiles by Y so they're always drawn back-to-front
        self.object_tiles.sort(key=lambda t: t[2])

    # ------------------------------------------------------------------
    def draw_floor(self, surface, camera_offset):
        """Call this BEFORE drawing sprites."""
        for img, world_pos in self.floor_tiles:
            screen_pos = world_pos - camera_offset
            surface.blit(img, screen_pos)

    def draw_objects(self, surface, camera_offset):
        """Call this AFTER drawing sprites (or interleave with Y-sort if needed)."""
        for img, world_pos, _ in self.object_tiles:
            screen_pos = world_pos - camera_offset
            surface.blit(img, screen_pos)
