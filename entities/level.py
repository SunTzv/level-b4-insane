import pygame
import os
from settings import *

# ---------------------------------------------------------------------------
def grid_to_screen(col, row):
    return (col - row) * TILE_W // 2, (col + row) * TILE_H // 2

def screen_to_grid(wx, wy):
    """Precise inverse of grid_to_screen — uses round() not int() to avoid edge drift."""
    u = wx / (TILE_W / 2)
    v = wy / (TILE_H / 2)
    return round((u + v) / 2), round((v - u) / 2)

# ---------------------------------------------------------------------------
TILE_DEFS = {
    'C': {'path': os.path.join('assets', 'floor_concrete.png'),              'size': (TILE_W, TILE_H), 'z': 0, 'solid': False},
    'P': {'path': os.path.join('assets', 'tiles', 'floor_parking_line.png'), 'size': (TILE_W, TILE_H), 'z': 0, 'solid': False},
    'W': {'path': os.path.join('assets', 'tiles', 'wall.png'),               'size': (TILE_W, 96),     'z': 1, 'solid': True},
    'I': {'path': os.path.join('assets', 'tiles', 'pillar.png'),             'size': (32, 80),         'z': 1, 'solid': True},
    'X': {'path': os.path.join('assets', 'tiles', 'barrier_closed.png'),     'size': (TILE_W, 48),     'z': 1, 'solid': False},
    'O': {'path': os.path.join('assets', 'tiles', 'barrier_open.png'),       'size': (TILE_W, 48),     'z': 1, 'solid': False},
    'E': {'path': os.path.join('assets', 'tiles', 'elevator_door.png'),      'size': (TILE_W, 80),     'z': 1, 'solid': True},
    '.': None,
}

FALLBACK = {
    'C': (55,55,55), 'P': (65,65,45), 'W': (75,75,75),
    'I': (85,85,85), 'X': (170,35,35), 'O': (35,170,35), 'E': (90,90,120),
}

# ---------------------------------------------------------------------------
# Map — 26 cols × 14 rows
#
# STRUCTURE:
#   Row 0:     Outer top wall
#   Row 1:     Pillar support row (I at cols 2,6,10,14,18,22)
#   Rows 2-3:  Top parking bays   (all P — no pillars inside)
#   Row 4:     Concrete separator + drive entry to top bays
#   Rows 5-7:  Main drive lane
#   Row 8:     Concrete separator + drive entry to bottom bays
#   Rows 9-10: Bottom parking bays (all P)
#   Row 11:    Pillar support row
#   Row 12:    Guard station approach (open concrete)
#   Row 13:    Bottom wall + barrier at col 11
#
# Pillar cols: 2, 6, 10, 14, 18, 22  (evenly spaced across inner 24 cols)
# ---------------------------------------------------------------------------

# Helper: build a 26-char row string
def _row(inner_24):
    assert len(inner_24) == 24, f"Inner must be 24 chars, got {len(inner_24)}: '{inner_24}'"
    return 'W' + inner_24 + 'W'

_PILLAR_ROW = 'CICCCICCCICCCICCCICCCICC'   # pillars at positions 0,4,8,12,16,20 within inner
_park_row   = 'C' + 'P' * 22 + 'C'         # full-width parking lane

LAYOUT = [
    _row('W' * 24),                          # 0  outer top (double wall for height)
    _row(_PILLAR_ROW),                       # 1  top pillar support row
    _row(_park_row),                         # 2  top parking bay (row A)
    _row(_park_row),                         # 3  top parking bay (row B)  ← 2 deep ✓
    _row('C' * 24),                          # 4  separator / approach to top bays
    _row('C' * 24),                          # 5  main drive lane
    _row('C' * 24),                          # 6  main drive lane
    _row('C' * 24),                          # 7  main drive lane
    _row('C' * 24),                          # 8  separator / approach to bottom bays
    _row(_park_row),                         # 9  bottom parking bay (row A)
    _row(_park_row),                         # 10 bottom parking bay (row B)  ← 2 deep ✓
    _row(_PILLAR_ROW),                       # 11 bottom pillar support row
    _row('C' * 24),                          # 12 guard station area (open!)
    'W' * 11 + 'X' + 'W' * 14,              # 13 bottom wall + barrier at col 11
]

# ---------------------  validate all rows are 26 chars  --------------------
for _i, _r in enumerate(LAYOUT):
    assert len(_r) == 26, f"Row {_i} is {len(_r)} chars (expected 26): '{_r}'"

# ---------------------------------------------------------------------------
# Constants used by main.py
# ---------------------------------------------------------------------------
PLAYER_SPAWN_GRID = (9, 12)      # guard station — open concrete, next to barrier
BARRIER_GRID      = (11, 13)
ENTRY_COL         = 11

_P_COLS = [2, 6, 10, 14, 18, 22]   # spot columns (left edge of each 3-ish-wide space)

def tile_center(col, row):
    sx, sy = grid_to_screen(col, row)
    return pygame.math.Vector2(sx + TILE_W // 2, sy + TILE_H // 2)

def make_parking_paths():
    """4-waypoint drive path for each of 12 parking spots."""
    paths = []
    wp0 = (ENTRY_COL, 12)   # just inside barrier
    for col in _P_COLS:     # top bays: park in row 2
        paths.append([wp0, (ENTRY_COL, 6), (col, 6), (col, 2)])
    for col in _P_COLS:     # bottom bays: park in row 10
        paths.append([wp0, (ENTRY_COL, 8), (col, 8), (col, 10)])
    return paths

PARKING_PATHS   = make_parking_paths()
ENTRY_WAIT_POS  = tile_center(ENTRY_COL, 15)   # outside the lot


# ---------------------------------------------------------------------------
def _make_fallback(key, w, h):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    c = FALLBACK.get(key, (80, 80, 80))
    if h == TILE_H:
        pygame.draw.polygon(surf, c, [(w//2,0),(w,h//2),(w//2,h),(0,h//2)])
    else:
        surf.fill((*c, 220))
    return surf


class TileMap:
    def __init__(self):
        self._load_images()
        self.floor_tiles     = []
        self.object_tiles    = []
        self.collision_rects = []
        self.dynamic         = {}
        self._build()

    # ------------------------------------------------------------------
    def _load_images(self):
        self.images = {}
        for key, defn in TILE_DEFS.items():
            if defn is None: continue
            w, h = defn['size']
            path = defn['path']
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (w, h))
            else:
                img = _make_fallback(key, w, h)

            # Pillar: crop bottom ~20 px to remove baked-in ground shadow
            if key == 'I':
                crop_h = h - 20
                cropped = pygame.Surface((w, crop_h), pygame.SRCALPHA)
                cropped.blit(img, (0, 0), area=(0, 0, w, crop_h))
                img = cropped

            self.images[key] = img

    # ------------------------------------------------------------------
    def _build(self):
        for r, row_str in enumerate(LAYOUT):
            for c, char in enumerate(row_str):
                defn = TILE_DEFS.get(char)
                if defn is None: continue
                img = self.images.get(char)
                if img is None: continue

                w, h = img.get_size()   # use actual cropped size
                sx, sy = grid_to_screen(c, r)
                pos = pygame.math.Vector2(sx, sy)

                if defn['z'] == 0:
                    self.floor_tiles.append((img, pos))
                else:
                    sort_y = sy + h
                    self.object_tiles.append((img, pos, sort_y))
                    if defn['solid']:
                        # Collision rect = ground diamond footprint of this tile
                        gx = sx + TILE_W // 2          # horizontal centre
                        gy = sy + TILE_H // 2           # isometric ground centre
                        rw, rh = TILE_W, TILE_H // 2
                        self.collision_rects.append(
                            pygame.Rect(gx - rw // 2, gy - rh // 2, rw, rh))

        self.object_tiles.sort(key=lambda t: t[2])

    def set_tile(self, col, row, char):
        self.dynamic[(col, row)] = char

    def is_solid_at(self, wx, wy):
        col, row = screen_to_grid(wx, wy)
        # Dynamic override first (e.g. barrier open/closed)
        char = self.dynamic.get((col, row))
        if char is None:
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
        for (c, r), char in self.dynamic.items():
            defn = TILE_DEFS.get(char)
            if defn and defn.get('z') == 1:
                img = self.images.get(char)
                if img:
                    sx, sy = grid_to_screen(c, r)
                    surface.blit(img, pygame.math.Vector2(sx, sy) - offset)
