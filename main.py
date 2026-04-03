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
from entities.level import TileMap, PARKING_SPOTS, GUARD_BOOTH_GRID, grid_to_screen, get_entry_pos, get_lane_pos

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def random_plate():
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    digits  = ''.join(random.choices(string.digits, k=4))
    return f"{letters}{digits}"

# ---------------------------------------------------------------------------
class Game:
    CARS_TO_END_DAY = random.randint(10, 15)  # how many cars trigger end of shift
    SPAWN_INTERVAL  = (12.0, 25.0)            # seconds between car arrivals

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Level B4 Insane")
        self.clock   = pygame.time.Clock()

        # Render surface — game draws here at half res, then scaled 2x
        self.render_surf = pygame.Surface((RENDER_W, RENDER_H))

        self.state_manager = StateManager()

        # Tilemap (built first so player can reference it)
        self.tilemap = TileMap()

        # Player — spawn inside guard booth
        gx, gy = grid_to_screen(*GUARD_BOOTH_GRID)
        spawn_x = gx + TILE_W // 2
        spawn_y = gy + TILE_H // 2
        self.player = Player(spawn_x, spawn_y)
        self.player.set_tilemap(self.tilemap)

        self.all_sprites = CameraGroup()
        self.all_sprites.add(self.player)

        # Car management
        self.npc_cars      = []          # list of NPCCar
        self.parked_spots  = set()       # indices into PARKING_SPOTS that are taken
        self.cars_arrived  = 0
        self.spawn_timer   = random.uniform(*self.SPAWN_INTERVAL)
        self.shift_over    = False
        self.anomaly_car   = None        # the car that won't leave

        # UI / Lighting
        self.ui       = UI(self.state_manager)
        self.lighting = LightingManager(RENDER_W, RENDER_H)
        self.lights   = []

    # -----------------------------------------------------------------------
    def _spawn_npc_car(self):
        """Spawn one NPC car at the entry point heading to a free parking spot."""
        free = [i for i in range(len(PARKING_SPOTS)) if i not in self.parked_spots]
        if not free:
            return

        spot_idx = random.choice(free)
        self.parked_spots.add(spot_idx)

        is_anomaly = (self.cars_arrived == self.CARS_TO_END_DAY - 1)  # last car = anomaly
        plate      = random_plate() if not is_anomaly else "---???---"

        car = NPCCar(
            entry_pos  = get_entry_pos(),
            lane_pos   = get_lane_pos(),
            park_pos   = PARKING_SPOTS[spot_idx],
            plate      = plate,
            is_anomaly = is_anomaly,
        )
        self.npc_cars.append(car)
        self.all_sprites.add(car)
        self.cars_arrived += 1

        if is_anomaly:
            self.anomaly_car = car

    # -----------------------------------------------------------------------
    def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)  # cap dt to avoid spiral

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    # Flashlight (Day 3+)
                    if event.key == pygame.K_f and self.state_manager.day >= 3:
                        self.player.flashlight_on = not self.player.flashlight_on

                    # Logbook toggle
                    if event.key == pygame.K_TAB:
                        self.ui.toggle_logbook()

                    # Terminal input
                    if self.ui.handle_event(event):
                        continue

                    # Interact (E)
                    if event.key == pygame.K_e and not self.ui.logbook_open:
                        self._handle_interact()

            self.update(dt)
            self.draw()

    # -----------------------------------------------------------------------
    def _handle_interact(self):
        player_pos = pygame.math.Vector2(self.player.rect.center)

        # Anomaly car creepy message (only after shift over)
        if self.shift_over and self.anomaly_car:
            dist = player_pos.distance_to(self.anomaly_car.rect.center)
            if dist < 80:
                self.ui.show_dialogue(self.anomaly_car.get_creepy_message(), duration=7.0)
                return

        # Enter / exit a drivable car
        if self.player.in_car:
            self.player.in_car = False
            self.player.current_car.is_driven = False
            self.player.rect.x -= 40
            self.player.current_car = None
            return

        for sprite in self.all_sprites:
            if isinstance(sprite, Car) and not isinstance(sprite, NPCCar):
                if getattr(sprite, 'doors_locked', False):
                    continue
                if player_pos.distance_to(sprite.rect.center) < 70:
                    self.player.in_car      = True
                    self.player.current_car = sprite
                    sprite.is_driven        = True
                    return

    # -----------------------------------------------------------------------
    def update(self, dt):
        # Pause when logbook open on Day 1
        if self.ui.logbook_open and self.state_manager.day == 1:
            self.ui.update(dt)
            return

        self.all_sprites.update(dt)
        self.ui.update(dt)

        # Car spawning (only while shift is running)
        if not self.shift_over and self.cars_arrived < self.CARS_TO_END_DAY:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self._spawn_npc_car()
                self.spawn_timer = random.uniform(*self.SPAWN_INTERVAL)

        # Check if all cars (except anomaly) are parked → shift over
        if not self.shift_over and self.cars_arrived >= self.CARS_TO_END_DAY:
            all_parked = all(c.state == NPCCar.STATE_PARKED
                             for c in self.npc_cars
                             if not c.is_anomaly)
            if all_parked:
                self.shift_over = True
                self.ui.show_dialogue(
                    "SHIFT OVER.\nONE VEHICLE REMAINS IN LOT B4.\nPLATES: ???", duration=8.0)

        # NIGHTMARE wrap
        if self.state_manager.state == GameState.NIGHTMARE:
            for sprite in self.all_sprites:
                if sprite.rect.x > RENDER_W + 800: sprite.rect.x = -800
                elif sprite.rect.x < -800: sprite.rect.x = RENDER_W + 800
                if sprite.rect.y > RENDER_H + 800: sprite.rect.y = -800
                elif sprite.rect.y < -800: sprite.rect.y = RENDER_H + 800

        # Lighting
        self.lights = []
        state = self.state_manager.state.name
        if not self.player.in_car:
            if state == 'NORMAL':
                self.lights.append({'pos': pygame.math.Vector2(self.player.rect.center), 'radius': 180})
            elif state == 'DECAY':
                self.lights.append({'pos': pygame.math.Vector2(self.player.rect.center), 'radius': 110})
        if self.player.flashlight_on and not self.player.in_car:
            self.lights.append({'pos': pygame.math.Vector2(self.player.rect.center), 'radius': 200})
        if self.player.in_car and self.player.current_car:
            self.lights.append({'pos': pygame.math.Vector2(self.player.current_car.rect.center), 'radius': 280})

        # Paranoia
        in_light = any(
            pygame.math.Vector2(self.player.rect.center).distance_to(l['pos']) < l['radius']
            for l in self.lights
        )
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

        # 1. Floor
        self.tilemap.draw_floor(rs, off)

        # 2. Sprites (Y-sorted)
        self.all_sprites.custom_draw(target, rs)

        # 3. Object tiles (walls / pillars / barriers)
        self.tilemap.draw_objects(rs, off)

        # 4. Lighting
        self.lighting.draw(rs, off, self.lights, self.state_manager)

        # 5. UI
        logged_count = sum(1 for c in self.npc_cars if c.logged)
        self.ui.draw(rs, car_count=self.cars_arrived,
                     cars_needed=self.CARS_TO_END_DAY,
                     shift_over=self.shift_over)

        # 6. Scale render surface 2x onto real screen
        pygame.transform.scale(rs, (WIDTH, HEIGHT), self.screen)
        pygame.display.flip()


if __name__ == "__main__":
    game = Game()
    game.run()
