import pygame
import sys
from settings import *
from state_manager import StateManager
from entities.player import Player
from entities.car import Car, AutonomousCar
from camera import CameraGroup
from ui import UI
from state_manager import GameState
from lighting import LightingManager
from entities.level import TileMap

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Level B4 Insane")
        self.clock = pygame.time.Clock()
        self.state_manager = StateManager()
        
        self.all_sprites = CameraGroup()
        self.player = Player(WIDTH // 2, HEIGHT // 2)
        self.all_sprites.add(self.player)
        
        self.car = Car(WIDTH // 2 + 100, HEIGHT // 2, "B4-INSN")
        self.all_sprites.add(self.car)
        
        self.auto_car = AutonomousCar(WIDTH // 2 - 300, HEIGHT // 2 + 300, "NO-PLAT", self.player)
        self.all_sprites.add(self.auto_car)
        
        self.ui = UI(self.state_manager)
        self.day_timer = 0
        self.day_durations = {1: 180, 2: 300, 3: 420, 4: 600, 5: 999999}
        self.lighting = LightingManager(WIDTH, HEIGHT)
        self.lights = []
        self.player.flashlight_on = False
        self.tilemap = TileMap()

    def run(self):
        while True:
            # Delta time in seconds
            dt = self.clock.tick(FPS) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f and self.state_manager.day >= 3:
                        self.player.flashlight_on = not self.player.flashlight_on
                        
                    if event.key == pygame.K_TAB:
                        self.ui.toggle_logbook()
                        
                    if self.ui.handle_event(event):
                        continue
                        
                    if event.key == pygame.K_e and not self.ui.logbook_open:
                        if self.player.in_car:
                            self.player.in_car = False
                            self.player.current_car.is_driven = False
                            self.player.rect.x -= 50
                            self.player.current_car = None
                        else:
                            for sprite in self.all_sprites:
                                if isinstance(sprite, Car):
                                    if getattr(sprite, 'doors_locked', False):
                                        continue
                                    dist = pygame.math.Vector2(self.player.rect.center).distance_to(sprite.rect.center)
                                    if dist < 80:
                                        self.player.in_car = True
                                        self.player.current_car = sprite
                                        sprite.is_driven = True
                                        break

            self.update(dt)
            self.draw()

    def update(self, dt):
        if self.ui.logbook_open and self.state_manager.day == 1:
            return  # Pause game on Day 1 when logbook is open
            
        self.all_sprites.update(dt)
        self.day_timer += dt
        
        current_day_duration = self.day_durations.get(self.state_manager.day, 999999)
        if self.day_timer >= current_day_duration:
            self.state_manager.day += 1
            self.day_timer = 0
            if self.state_manager.day == 3:
                self.state_manager.set_state(GameState.DECAY)
            if self.state_manager.day == 5:
                self.state_manager.set_state(GameState.NIGHTMARE)
                
        # NIGHTMARE Labyrinth Wrap
        if self.state_manager.state == GameState.NIGHTMARE:
            for sprite in self.all_sprites:
                if sprite.rect.x > WIDTH + 500: sprite.rect.x = -500
                elif sprite.rect.x < -500: sprite.rect.x = WIDTH + 500
                if sprite.rect.y > HEIGHT + 500: sprite.rect.y = -500
                elif sprite.rect.y < -500: sprite.rect.y = HEIGHT + 500
                
        # Lighting calculation
        self.lights = []
        if self.player.flashlight_on and not self.player.in_car:
            self.lights.append({'pos': pygame.math.Vector2(self.player.rect.center), 'radius': 150})
        if self.player.in_car:
            self.lights.append({'pos': pygame.math.Vector2(self.player.current_car.rect.center), 'radius': 250})
            
        # Paranoia
        in_light = False
        for light in self.lights:
            if pygame.math.Vector2(self.player.rect.center).distance_to(light['pos']) < light['radius']:
                in_light = True
                
        if not in_light and not self.player.in_car:
            self.state_manager.paranoia_float += dt * 5
        else:
            self.state_manager.paranoia_float -= dt * 10
            self.state_manager.paranoia_float = max(0.0, self.state_manager.paranoia_float)

    def draw(self):
        self.screen.fill(BLACK)
        
        target = self.player.current_car if self.player.in_car else self.player
        
        # 1. Floor tiles (drawn first, behind everything)
        self.tilemap.draw(self.screen, self.all_sprites.offset)
        
        # 2. Y-sorted sprites (player, cars)
        self.all_sprites.custom_draw(target)
        
        # 3. Darkness / lighting overlay
        self.lighting.draw(self.screen, self.all_sprites.offset, self.lights, self.state_manager)
        
        # 4. UI on top of everything
        self.ui.draw(self.screen)
        
        pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()
