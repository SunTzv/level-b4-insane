import pygame
import os
from settings import *

# ---------------------------------------------------------------------------
# Coordinate conversion
# ---------------------------------------------------------------------------
def grid_to_screen(col, row):
    x = (col - row) * TILE_W // 2
    y = (col + row) * TILE_H // 2
    return x, y

def screen_to_grid(sx, sy):
    """Approximate inverse — used for collision grid lookup."""
    col = (sx / (TILE_W / 2) + sy / (TILE_H / 2)) / 2
    row = (sy / (TILE_H / 2) - sx / (TILE_W / 2)) / 2
    return int(col), int(row)

# ---------------------------------------------------------------------------
# Tile definitions
# ---------------------------------------------------------------------------
TILE_DEFS = {
    'C': {'path': os.path.join('assets', 'floor_concrete.png'),              'size': (TILE_W, TILE_H), 'z': 0, 'solid': False},
    'P': {'path': os.path.join('assets', 'tiles', 'floor_parking_line.png'), 'size': (TILE_W, TILE_H), 'z': 0, 'solid': False},
    'W': {'path': os.path.join('assets', 'tiles', 'wall.png'),               'size': (TILE_W, 96),     'z': 1, 'solid': True},
    'I': {'path': os.path.join('assets', 'tiles', 'pillar.png'),             'size': (32,    80),      'z': 1, 'solid': True},
    'X': {'path': os.path.join('assets', 'tiles', 'barrier_closed.png'),     'size': (TILE_W, 48),     'z': 1, 'solid': True},
    'O': {'path': os.path.join('assets', 'tiles', 'barrier_open.png'),       'size': (TILE_W, 48),     'z': 1, 'solid': False},
    'E': {'path': os.path.join('assets', 'tiles', 'elevator_door.png'),      'size': (TILE_W, 80),     'z': 1, 'solid': True},
    '.': None,
}

FALLBACK_COLORS = {
    'C': (60, 60, 60), 'P': (70, 70, 50), 'W': (80, 80, 80),
    'I': (90, 90, 90), 'X': (180, 40, 40), 'O': (40, 180, 40),
    'E': (100, 100, 130),
}

# ---------------------------------------------------------------------------
# Map layout  (26 cols wide, 17 rows tall)
# Guard booth = small walled enclosure near barrier (rows 13-14, cols 2-4)
# Barrier X   = row 16, col 13
# Parking spots: 'P' tiles — rows 2,3 (top bays) and rows 9,10 (bottom bays)
# Collidable:  W, I, X
# ---------------------------------------------------------------------------
LAYOUT = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWW",  # 0  outer top wall         (26)
    "WCCCCCCCCCCCCCCCCCCCCCCCCW",  # 1
    "WCPPICPPICPPICPPICPPICPPCW",  # 2  top parking bays
    "WCPPICPPICPPICPPICPPICPPCW",  # 3  top parking bays
    "WCCCCCCCCCCCCCCCCCCCCCCCCW",  # 4
    "WCCCCCCCCCCCCCCCCCCCCCCCCW",  # 5  main drive lane
    "WCCCCCCCCCCCCCCCCCCCCCCCCW",  # 6  main drive lane
    "WCCCCCCCCCCCCCCCCCCCCCCCCW",  # 7
    "WCCCCCCCCCCCCCCCCCCCCCCCCW",  # 8
    "WCPPICPPICPPICPPICPPICPPCW",  # 9  bottom parking bays
    "WCPPICPPICPPICPPICPPICPPCW",  # 10 bottom parking bays
    "WCCCCCCCCCCCCCCCCCCCCCCCCW",  # 11
    "WCCCCCCCCCCCCCCCCCCCCCCCCW",  # 12 approach lane
    "WCCWWWCCCCCCCCCCCCCCCCCCCW",  # 13 guard booth top wall
    "WCCWCWCCCCCCCCCCCCCCCCCCCW",  # 14 guard booth (W.W = walls, C = inside)
    "WCCCCCCCCCCCCCCCCCCCCCCCCW",  # 15 approach to barrier
    "WWWWWWWWWWWWWXWWWWWWWWWWWW",  # 16 bottom wall + barrier at col 13
]

# Guard booth inside position (player starts here): grid (4, 14)
GUARD_BOOTH_GRID = (4, 14)

# Parking spot grid positions (center col of each 2-wide bay, row index)
# Top bays: row 2, cols 2,6,10,14,18,22
# Bottom bays: row 9, same cols
_P_COLS = [2, 6, 10, 14, 18, 22]
PARKING_SPOTS = (
    [grid_to_screen(c, 2) for c in _P_COLS] +
    [grid_to_screen(c, 9) for c in _P_COLS]
)

# Entry point for NPC cars (just below the barrier in world space)
def get_entry_pos():
    sx, sy = grid_to_screen(13, 16)
    return pygame.math.Vector2(sx + TILE_W // 2, sy + TILE_H * 2)

# Lane waypoint inside the lot (cars head here first after entering)
def get_lane_pos():
    sx, sy = grid_to_screen(13, 14)
    return pygame.math.Vector2(sx + TILE_W // 2, sy + TILE_H // 2)


def _make_fallback(key, w, h):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    color = FALLBACK_COLORS.get(key, (80, 80, 80))
    if h == TILE_H:
        pygame.draw.polygon(surf, color, [
            (w//2, 0), (w, h//2), (w//2, h), (0, h//2)])
    else:
        surf.fill((*color, 220))
    return surf


class TileMap:
    def __init__(self):
        self._load_images()
        self.floor_tiles   = []
        self.object_tiles  = []   # (img, world_pos_v2, sort_y)
        self.collision_rects = [] # pygame.Rect in world space (for solid tiles)
        self._build_tiles()

    def _load_images(self):
        self.images = {}
        for key, defn in TILE_DEFS.items():
            if defn is None:
                continue
            w, h = defn['size']
            path  = defn['path']
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (w, h))
            else:
                img = _make_fallback(key, w, h)
            self.images[key] = img

    def _build_tiles(self):
        for row_idx, row_str in enumerate(LAYOUT):
            for col_idx, char in enumerate(row_str):
                defn = TILE_DEFS.get(char)
                if defn is None:
                    continue
                img = self.images.get(char)
                if img is None:
                    continue
                w, h = defn['size']
                sx, sy = grid_to_screen(col_idx, row_idx)
                pos = pygame.math.Vector2(sx, sy)

                if defn['z'] == 0:
                    self.floor_tiles.append((img, pos))
                else:
                    sort_y = sy + h
                    self.object_tiles.append((img, pos, sort_y))
                    if defn['solid']:
                        # Collision rect = diamond ground footprint of tile
                        cx = sx + w // 2
                        cy = sy + TILE_H // 2
                        self.collision_rects.append(
                            pygame.Rect(cx - TILE_W//2, cy - TILE_H//4,
                                        TILE_W, TILE_H//2)
                        )
        self.object_tiles.sort(key=lambda t: t[2])

    def is_solid_at(self, wx, wy):
        """Quick grid lookup — True if the world point sits on a solid tile."""
        col, row = screen_to_grid(wx, wy)
        if row < 0 or row >= len(LAYOUT): return True
        if col < 0 or col >= len(LAYOUT[row]): return True
        char = LAYOUT[row][col]
        defn = TILE_DEFS.get(char)
        return defn is not None and defn.get('solid', False)

    def draw_floor(self, surface, offset):
        for img, pos in self.floor_tiles:
            surface.blit(img, pos - offset)

    def draw_objects(self, surface, offset):
        for img, pos, _ in self.object_tiles:
            surface.blit(img, pos - offset)
