import pygame
import random
from settings import *

class UI:
    def __init__(self, state_manager):
        self.state_manager = state_manager
        # Fallback to monospace if Courier New isn't available
        self.font = pygame.font.SysFont("Courier New", 24, bold=True)
        self.logbook_open = False
        self.current_input = ""
        self.logs = []
        
        self.terminal_rect = pygame.Rect(WIDTH // 4, HEIGHT // 4, WIDTH // 2, HEIGHT // 2)
    
    def toggle_logbook(self):
        self.logbook_open = not self.logbook_open
    
    def handle_event(self, event):
        if not self.logbook_open:
            return False
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.current_input.strip() != "":
                    self.logs.append(self.current_input)
                    self.current_input = ""
            elif event.key == pygame.K_BACKSPACE:
                self.current_input = self.current_input[:-1]
            elif event.key != pygame.K_TAB:
                if event.unicode.isprintable():
                    self.current_input += event.unicode
            return True
        return False
                    
    def draw(self, screen):
        if self.logbook_open:
            # UI Glitch / Paranoia effect
            jx, jy = 0, 0
            if self.state_manager.paranoia_float > 20: # Example threshold
                intensity = min(15, int((self.state_manager.paranoia_float - 20) / 2))
                jx = random.randint(-intensity, intensity)
                jy = random.randint(-intensity, intensity)
            
            draw_rect = self.terminal_rect.move(jx, jy)
            
            pygame.draw.rect(screen, (0, 0, 40), draw_rect)
            pygame.draw.rect(screen, (200, 200, 200), draw_rect, 4)
            
            title_surf = self.font.render(f"B4 PARKING LOG - DAY {self.state_manager.day}", True, (0, 255, 0))
            screen.blit(title_surf, (draw_rect.x + 10, draw_rect.y + 10))
            
            y_offset = 50
            start_index = max(0, len(self.logs) - 8)
            for log in self.logs[start_index:]:
                log_surf = self.font.render("> " + log, True, (0, 255, 0))
                screen.blit(log_surf, (draw_rect.x + 10, draw_rect.y + y_offset))
                y_offset += 30
                
            input_surf = self.font.render(f"> {self.current_input}_", True, (0, 255, 0))
            screen.blit(input_surf, (draw_rect.x + 10, draw_rect.bottom - 40))
