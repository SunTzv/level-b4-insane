import pygame
import random
from settings import *

class UI:
    def __init__(self, state_manager):
        self.state_manager  = state_manager
        self.font_large = pygame.font.SysFont("Courier New", 14, bold=True)
        self.font_small = pygame.font.SysFont("Courier New", 11, bold=True)
        self.logbook_open   = False
        self.current_input  = ""
        self.logs           = []
        self.terminal_rect  = pygame.Rect(RENDER_W // 4, RENDER_H // 4,
                                          RENDER_W // 2, RENDER_H // 2)
        # Dialogue
        self.dialogue_lines  = []
        self.dialogue_timer  = 0.0
        self.dialogue_active = False

    # ------------------------------------------------------------------
    def show_dialogue(self, text: str, duration: float = 6.0):
        self.dialogue_lines  = text.split('\n')
        self.dialogue_timer  = duration
        self.dialogue_active = True

    def toggle_logbook(self):
        self.logbook_open = not self.logbook_open

    # ------------------------------------------------------------------
    def handle_event(self, event):
        if not self.logbook_open:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.current_input.strip():
                    self.logs.append(self.current_input.strip().upper())
                    self.current_input = ""
            elif event.key == pygame.K_BACKSPACE:
                self.current_input = self.current_input[:-1]
            elif event.key != pygame.K_TAB and event.unicode.isprintable():
                self.current_input += event.unicode
            return True
        return False

    # ------------------------------------------------------------------
    def update(self, dt):
        if self.dialogue_active:
            self.dialogue_timer -= dt
            if self.dialogue_timer <= 0:
                self.dialogue_active = False

    # ------------------------------------------------------------------
    def draw(self, surface, car_count=0, cars_needed=10, shift_over=False):
        """Draw onto the render surface (RENDER_W x RENDER_H)."""
        self._draw_hud(surface, car_count, cars_needed, shift_over)
        if self.logbook_open:
            self._draw_terminal(surface)
        if self.dialogue_active:
            self._draw_dialogue(surface)

    # -- HUD -----------------------------------------------------------
    def _draw_hud(self, surface, car_count, cars_needed, shift_over):
        pad = 6
        lines = [
            (f"DAY  {self.state_manager.day}",         (0, 255, 80)),
            (f"CARS {car_count:02d}/{cars_needed:02d}", (0, 255, 80)),
            ("** SHIFT OVER **" if shift_over else "SHIFT IN PROGRESS",
             (255, 80, 80) if shift_over else (160, 160, 160)),
        ]
        for i, (text, color) in enumerate(lines):
            surf = self.font_small.render(text, True, color)
            surface.blit(surf, (pad, pad + i * 14))

    # -- Terminal ------------------------------------------------------
    def _draw_terminal(self, surface):
        jx, jy = 0, 0
        if self.state_manager.paranoia_float > 20:
            t = min(15, int((self.state_manager.paranoia_float - 20) / 2))
            jx, jy = random.randint(-t, t), random.randint(-t, t)
        r = self.terminal_rect.move(jx, jy)

        pygame.draw.rect(surface, (0, 0, 30), r)
        pygame.draw.rect(surface, (0, 200, 60), r, 2)
        hdr = self.font_large.render(
            f"B4 PARKING LOG  DAY {self.state_manager.day}", True, (0, 255, 80))
        surface.blit(hdr, (r.x + 5, r.y + 5))

        y = r.y + 22
        for log in self.logs[-(max(1,(r.height-40)//12)):]:
            surface.blit(self.font_small.render("> " + log, True, (0, 220, 60)),
                         (r.x + 5, y))
            y += 12

        inp = self.font_small.render(f"> {self.current_input}_", True, (0, 255, 80))
        surface.blit(inp, (r.x + 5, r.bottom - 16))
        tip = self.font_small.render("[TAB] CLOSE  [ENTER] SUBMIT", True, (60, 120, 60))
        surface.blit(tip, (r.x + 5, r.bottom - 28))

    # -- Dialogue box --------------------------------------------------
    def _draw_dialogue(self, surface):
        bw, bh = RENDER_W - 40, 18 * (len(self.dialogue_lines) + 1) + 12
        bx = 20
        by = RENDER_H - bh - 20
        pygame.draw.rect(surface, (5, 5, 5), (bx, by, bw, bh))
        pygame.draw.rect(surface, (180, 20, 20), (bx, by, bw, bh), 2)
        for i, line in enumerate(self.dialogue_lines):
            surf = self.font_large.render(line, True, (220, 50, 50))
            surface.blit(surf, (bx + 8, by + 8 + i * 16))
