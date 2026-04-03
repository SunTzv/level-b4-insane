import pygame
import os
from settings import *

# ---------------------------------------------------------------------------
def grid_to_screen(col, row):
    return (col - row) * TILE_W // 2, (col + row) * TILE_H // 2

def screen_to_grid(sx, sy):
    col = (sx / (TILE_W / 2) + sy / (TILE_H / 2)) / 2
    row = (sy / (TILE_H / 2) - sx / (TILE_W / 2)) / 2
    return int(col), int(row)

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
    'C': (60,60,60),'P': (70,70,50),'W': (80,80,80),
    'I': (90,90,90),'X': (180,40,40),'O': (40,180,40),'E': (100,100,130),
}

# ---------------------------------------------------------------------------
# Map  — 26 cols × 14 rows
# Guard station: area around col 8-9, row 11 (marked with 'I' pillar at col 7)
# Barrier: col 11, row 13 (bottom wall)
# Player spawns at col 9, row 11 — right next to guard pillar, adjacent to barrier
# ---------------------------------------------------------------------------
LAYOUT = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWW",  # 0  top wall
    "WCCCCCCCCCCCCCCCCCCCCCCCCW",  # 1
    "WCPPICPPICPPICPPICPPICPPCW",  # 2  top parking bays
    "WCPPICPPICPPICPPICPPICPPCW",  # 3
    "WCCCCCCCCCCCCCCCCCCCCCCCCW",  # 4
    "WCCCCCCCCCCCCCCCCCCCCCCCCW",  # 5  main drive lane
    "WCCCCCCCCCCCCCCCCCCCCCCCCW",  # 6
    "WCCCCCCCCCCCCCCCCCCCCCCCCW",  # 7
    "WCPPICPPICPPICPPICPPICPPCW",  # 8  bottom parking bays
    "WCPPICPPICPPICPPICPPICPPCW",  # 9
    "WCCCCCCCCCCCCCCCCCCCCCCCCW",  # 10
    "WCCCCCCCCCCCCCCCCCCCCCCCCW",  # 11 approach lane  ← player + guard area
    "WCCCCCCICCCCCCCCCCCCCCCCW",   # 12 guard pillar 'I' at col 7
    "WWWWWWWWWWWXWWWWWWWWWWWWWW",  # 13 bottom wall, barrier 'X' at col 11
]

# Guard station — player spawns here (open concrete, pillar to the left)
PLAYER_SPAWN_GRID = (9, 11)

# Barrier tile position
BARRIER_GRID      = (11, 13)

# Lane col that the entry uses
ENTRY_COL = 11

# Parking spot grid column anchors (left col of each 2-tile wide bay)
# Row "WCPPICPPICPPICPPICPPICPPCW":
#   P at: 2,3 | 6,7 | 10,11 | 14,15 | 18,19 | 22,23
_P_COLS = [2, 6, 10, 14, 18, 22]

# 4-waypoint paths for each of the 12 parking spots
def make_parking_paths():
    paths = []
    wp0_grid = (ENTRY_COL, 12)   # just inside barrier

    for col in _P_COLS:
        # Top bay (row 3): enter → main lane row 6 → target col → park row 3
        wps = [
            wp0_grid,
            (ENTRY_COL, 6),
            (col, 6),
            (col, 3),
        ]
        paths.append([(c, r) for c, r in wps])

    for col in _P_COLS:
        # Bottom bay (row 8): enter → lower lane row 10 → target col → park row 8
        wps = [
            wp0_grid,
            (ENTRY_COL, 10),
            (col, 10),
            (col, 8),
        ]
        paths.append([(c, r) for c, r in wps])

    return paths

PARKING_PATHS = make_parking_paths()   # list of 12 paths, each a list of (col,row)

# Convenience: world-centre of a tile
def tile_center(col, row):
    sx, sy = grid_to_screen(col, row)
    return pygame.math.Vector2(sx + TILE_W // 2, sy + TILE_H // 2)

# Where cars wait outside the barrier
ENTRY_WAIT_POS = tile_center(ENTRY_COL, 15)

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
        self.floor_tiles    = []
        self.object_tiles   = []
        self.collision_rects = []
        # Dynamic tile override: {(col,row): char} — for barrier open/close
        self.dynamic = {}
        self._build_tiles()

    def set_tile(self, col, row, char):
        """Change a tile at runtime (e.g. open/close barrier)."""
        self.dynamic[(col, row)] = char

    def _load_images(self):
        self.images = {}
        for key, defn in TILE_DEFS.items():
            if defn is None: continue
            w, h = defn['size']
            img = (pygame.image.load(defn['path']).convert_alpha()
                   if os.path.exists(defn['path'])
                   else _make_fallback(key, w, h))
            self.images[key] = pygame.transform.scale(img, (w, h))

    def _build_tiles(self):
        for r, row_str in enumerate(LAYOUT):
            for c, char in enumerate(row_str):
                self._register_tile(c, r, char)
        self.object_tiles.sort(key=lambda t: t[2])

    def _register_tile(self, c, r, char):
        defn = TILE_DEFS.get(char)
        if defn is None: return
        img = self.images.get(char)
        if img is None: return
        w, h = defn['size']
        sx, sy = grid_to_screen(c, r)
        pos = pygame.math.Vector2(sx, sy)
        if defn['z'] == 0:
            self.floor_tiles.append((img, pos))
        else:
            self.object_tiles.append((img, pos, sy + h))
            if defn['solid']:
                cx, cy = sx + w//2, sy + TILE_H//2
                self.collision_rects.append(
                    pygame.Rect(cx - TILE_W//2, cy - TILE_H//4, TILE_W, TILE_H//2))

    def is_solid_at(self, wx, wy):
        col, row = screen_to_grid(wx, wy)
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
        # Merge static + dynamic object tiles
        for img, pos, _ in self.object_tiles:
            surface.blit(img, pos - offset)
        # Draw dynamic tile overrides on top
        for (c, r), char in self.dynamic.items():
            defn = TILE_DEFS.get(char)
            if defn is None or defn['z'] != 1: continue
            img = self.images.get(char)
            if img is None: continue
            sx, sy = grid_to_screen(c, r)
            surface.blit(img, pygame.math.Vector2(sx, sy) - offset)
