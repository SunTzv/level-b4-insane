import pygame
import sys
import random
import string
from settings import *
from state_manager import StateManager, GameState
from entities.player import Player
from entities.car import Car, NPCCar, AutonomousCar
from camera import CameraGroup
from ui import UI
from lighting import LightingManager
from entities.level import (TileMap, PLAYER_SPAWN_GRID, BARRIER_GRID,
                             ENTRY_WAIT_POS, PARKING_PATHS, tile_center,
                             grid_to_screen, ENTRY_COL)

# ---------------------------------------------------------------------------
def random_plate():
    return (''.join(random.choices(string.ascii_uppercase, k=2))
            + ''.join(random.choices(string.digits, k=4)))

BARRIER_INTERACT_DIST = 80   # world pixels

class Game:
    CARS_TO_END = random.randint(10, 15)
    QUEUE_INTERVAL = (18.0, 30.0)     # seconds between cars arriving at barrier

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Level B4 Insane")
        self.clock = pygame.time.Clock()
        self.render_surf = pygame.Surface((RENDER_W, RENDER_H))

        self.state_manager = StateManager()
        self.tilemap = TileMap()

        # Player — spawns at guard station beside pillar, facing barrier
        sx, sy = grid_to_screen(*PLAYER_SPAWN_GRID)
        self.player = Player(sx + TILE_W // 2, sy + TILE_H // 2)
        self.player.set_tilemap(self.tilemap)

        self.all_sprites = CameraGroup()
        self.all_sprites.add(self.player)

        # --- Car system ---
        self._all_spot_indices = list(range(len(PARKING_PATHS)))
        random.shuffle(self._all_spot_indices)
        self._spot_queue  = self._all_spot_indices[:]   # spots to assign

        self.npc_cars     = []
        self.waiting_car  = None    # car sitting at barrier
        self.cars_arrived = 0       # cars that have entered the lot
        self.queue_timer  = 5.0     # first car arrives quickly
        self.shift_over   = False
        self.anomaly_car  = None

        # Barrier state
        self.barrier_open       = False
        self.barrier_close_timer = 0.0

        # Plate notification
        self.plate_notif         = ""
        self.plate_notif_timer   = 0.0

        self.ui       = UI(self.state_manager)
        self.lighting = LightingManager(RENDER_W, RENDER_H)
        self.lights   = []

    # -----------------------------------------------------------------------
    def _queue_next_car(self):
        """Spawn a new car at the barrier waiting position."""
        if not self._spot_queue:
            return
        spot_idx  = self._spot_queue.pop(0)
        is_anomaly = (self.cars_arrived + 1 == self.CARS_TO_END)
        plate     = "---???---" if is_anomaly else random_plate()
        path      = PARKING_PATHS[spot_idx]

        car = NPCCar(
            entry_pos  = ENTRY_WAIT_POS,
            path_grids = path,
            plate      = plate,
            is_anomaly = is_anomaly,
            spot_idx   = spot_idx,
        )
        self.waiting_car = car
        self.npc_cars.append(car)
        self.all_sprites.add(car)
        if is_anomaly:
            self.anomaly_car = car

    def _open_barrier(self):
        self.barrier_open = True
        self.barrier_close_timer = 3.5   # seconds barrier stays open
        self.tilemap.set_tile(*BARRIER_GRID, 'O')

        if self.waiting_car and self.waiting_car.state == NPCCar.WAIT:
            self.waiting_car.allow_enter()
            self.cars_arrived += 1
            # Show plate notification
            self.plate_notif       = f"INCOMING: {self.waiting_car.plate}"
            self.plate_notif_timer = 6.0
            self.waiting_car = None   # no longer "waiting"
            self.queue_timer  = random.uniform(*self.QUEUE_INTERVAL)

    # -----------------------------------------------------------------------
    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f and self.state_manager.day >= 3:
                        self.player.flashlight_on = not self.player.flashlight_on
                    if event.key == pygame.K_TAB:
                        self.ui.toggle_logbook()
                    if self.ui.handle_event(event):
                        continue
                    if event.key == pygame.K_e and not self.ui.logbook_open:
                        self._handle_interact()
            self.update(dt)
            self.draw()

    # -----------------------------------------------------------------------
    def _handle_interact(self):
        pv = pygame.math.Vector2(self.player.rect.center)

        # Barrier interaction — open to let waiting car in
        bx, by = grid_to_screen(*BARRIER_GRID)
        barrier_center = pygame.math.Vector2(bx + TILE_W//2, by + TILE_H//2)
        if pv.distance_to(barrier_center) < BARRIER_INTERACT_DIST:
            if self.waiting_car and not self.barrier_open:
                self._open_barrier()
            elif not self.waiting_car:
                self.ui.show_dialogue("NO VEHICLE WAITING.", duration=2.5)
            return

        # Anomaly car creepy message (shift over)
        if self.shift_over and self.anomaly_car:
            if pv.distance_to(pygame.math.Vector2(self.anomaly_car.rect.center)) < 80:
                self.ui.show_dialogue(self.anomaly_car.creepy_message(), duration=7.0)
                return

        # Enter / exit player-drivable car
        if self.player.in_car:
            self.player.in_car = False
            self.player.current_car.is_driven = False
            self.player.rect.x -= 40
            self.player.current_car = None
            return
        for spr in self.all_sprites:
            if isinstance(spr, Car) and not isinstance(spr, NPCCar):
                if not getattr(spr, 'doors_locked', False):
                    if pv.distance_to(pygame.math.Vector2(spr.rect.center)) < 70:
                        self.player.in_car      = True
                        self.player.current_car = spr
                        spr.is_driven           = True
                        return

    # -----------------------------------------------------------------------
    def update(self, dt):
        if self.ui.logbook_open and self.state_manager.day == 1:
            self.ui.update(dt)
            return

        self.all_sprites.update(dt)
        self.ui.update(dt)

        # Barrier auto-close
        if self.barrier_open:
            self.barrier_close_timer -= dt
            if self.barrier_close_timer <= 0:
                self.barrier_open = False
                self.tilemap.set_tile(*BARRIER_GRID, 'X')

        # Plate notification timer
        if self.plate_notif_timer > 0:
            self.plate_notif_timer -= dt

        # Queue next car (only if no car currently waiting)
        if (not self.shift_over
                and self.waiting_car is None
                and self.cars_arrived < self.CARS_TO_END):
            self.queue_timer -= dt
            if self.queue_timer <= 0:
                self._queue_next_car()

        # Shift end detection
        if (not self.shift_over
                and self.cars_arrived >= self.CARS_TO_END
                and self.waiting_car is None):
            all_in = all(c.state == NPCCar.PARKED
                         for c in self.npc_cars if not c.is_anomaly)
            if all_in:
                self.shift_over = True
                self.ui.show_dialogue(
                    "SHIFT OVER.\nONE VEHICLE REMAINS IN LOT B4.\nAPPROACH IT.", duration=8.0)

        # Lighting
        self.lights = []
        state = self.state_manager.state.name
        if not self.player.in_car:
            r = 180 if state == 'NORMAL' else 110 if state == 'DECAY' else 0
            if r: self.lights.append({'pos': pygame.math.Vector2(self.player.rect.center), 'radius': r})
        if self.player.flashlight_on and not self.player.in_car:
            self.lights.append({'pos': pygame.math.Vector2(self.player.rect.center), 'radius': 200})
        if self.player.in_car and self.player.current_car:
            self.lights.append({'pos': pygame.math.Vector2(self.player.current_car.rect.center), 'radius': 280})

        in_light = any(
            pygame.math.Vector2(self.player.rect.center).distance_to(l['pos']) < l['radius']
            for l in self.lights)
        if not in_light and not self.player.in_car:
            self.state_manager.paranoia_float += dt * 5
        else:
            self.state_manager.paranoia_float = max(
                0.0, self.state_manager.paranoia_float - dt * 10)

    # -----------------------------------------------------------------------
    def draw(self):
        rs = self.render_surf
        rs.fill(BLACK)

        target = self.player.current_car if self.player.in_car else self.player
        self.all_sprites.update_offset(target)
        off = self.all_sprites.offset

        self.tilemap.draw_floor(rs, off)
        self.all_sprites.custom_draw(target, rs)
        self.tilemap.draw_objects(rs, off)
        self.lighting.draw(rs, off, self.lights, self.state_manager)

        # Plate notification overlay
        if self.plate_notif_timer > 0:
            font = pygame.font.SysFont("Courier New", 13, bold=True)
            surf = font.render(self.plate_notif, True, (255, 220, 0))
            rs.blit(surf, (RENDER_W//2 - surf.get_width()//2, 10))

        self.ui.draw(rs,
                     car_count    = self.cars_arrived,
                     cars_needed  = self.CARS_TO_END,
                     shift_over   = self.shift_over)

        # Barrier indicator (top-right corner)
        font_s = pygame.font.SysFont("Courier New", 10, bold=True)
        b_text = "[E] OPEN BARRIER" if self.waiting_car else "NO VEHICLE QUEUED"
        b_col  = (255, 180, 0) if self.waiting_car else (100, 100, 100)
        rs.blit(font_s.render(b_text, True, b_col), (RENDER_W - 140, 6))

        pygame.transform.scale(rs, (WIDTH, HEIGHT), self.screen)
        pygame.display.flip()


if __name__ == "__main__":
    game = Game()
    game.run()
