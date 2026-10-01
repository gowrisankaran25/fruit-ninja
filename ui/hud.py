"""
HUD — Modern Glassmorphic Heads-Up Display drawn over the game.
Renders score, high score, lives, level progress bar, combo flares, and power-up badges.
"""
import pygame
import math
from config import Colors, POWERUP_TYPES, SCREEN_WIDTH


class HUD:
    """Renders a sleek, modern glassmorphic HUD overlay."""

    def __init__(self):
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self.font_combo = None
        self.font_badge = None
        self._initialized = False

    def _init_fonts(self):
        if self._initialized:
            return
        self.font_large = pygame.font.Font(None, 44)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_badge = pygame.font.Font(None, 20)
        self.font_combo = pygame.font.Font(None, 68)
        self._initialized = True

    def draw(self, surface, scoring, lives, combo, level, powerup_sys, timer_remaining=None):
        self._init_fonts()

        # ── Glassmorphic Top Bar Container ──
        bar_w = SCREEN_WIDTH - 40
        bar_h = 65
        bar_x = 20
        bar_y = 12

        # Translucent glass panel
        glass = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        pygame.draw.rect(glass, (12, 14, 35, 175), (0, 0, bar_w, bar_h), border_radius=16)
        pygame.draw.rect(glass, (100, 150, 255, 60), (0, 0, bar_w, bar_h), 2, border_radius=16)
        # Highlight rim
        pygame.draw.line(glass, (255, 255, 255, 40), (16, 2), (bar_w - 16, 2), width=1)
        surface.blit(glass, (bar_x, bar_y))

        # ── Score & High Score (Top-Left) ──
        score_lbl = self.font_badge.render("SCORE", True, (160, 170, 200))
        surface.blit(score_lbl, (40, bar_y + 8))

        score_val = self.font_large.render(f"{scoring.score:,}", True, Colors.WHITE)
        surface.blit(score_val, (40, bar_y + 24))

        # High Score Badge
        hi_bg = pygame.Surface((105, 24), pygame.SRCALPHA)
        pygame.draw.rect(hi_bg, (255, 215, 0, 40), (0, 0, 105, 24), border_radius=12)
        pygame.draw.rect(hi_bg, (255, 215, 0, 140), (0, 0, 105, 24), 1, border_radius=12)
        surface.blit(hi_bg, (210, bar_y + 22))

        hi_txt = self.font_badge.render(f"BEST: {scoring.high_score:,}", True, Colors.GOLD)
        surface.blit(hi_txt, (218, bar_y + 27))

        # ── Level Badge & Progress Bar (Center) ──
        lvl_lbl = self.font_medium.render(f"LVL {level.level} • {level.label.upper()}", True, Colors.CYAN)
        lvl_rect = lvl_lbl.get_rect(center=(SCREEN_WIDTH // 2, bar_y + 22))
        surface.blit(lvl_lbl, lvl_rect)

        # Level progress bar
        prog_w = 160
        prog_h = 6
        prog_x = SCREEN_WIDTH // 2 - prog_w // 2
        prog_y = bar_y + 45
        progress = getattr(level, 'progress', 0.0)

        pygame.draw.rect(surface, (30, 35, 60), (prog_x, prog_y, prog_w, prog_h), border_radius=3)
        if progress > 0:
            pygame.draw.rect(surface, Colors.CYAN, (prog_x, prog_y, int(prog_w * progress), prog_h), border_radius=3)

        # ── Lives (Top-Right) ──
        lives_x = SCREEN_WIDTH - 45
        for i in range(lives.max_lives):
            is_active = i < lives.lives
            cx = lives_x - i * 38
            cy = bar_y + 32

            color = Colors.RED if is_active else (60, 65, 85)
            # Glowing aura for active hearts
            if is_active:
                aura = pygame.Surface((32, 32), pygame.SRCALPHA)
                pygame.draw.circle(aura, (255, 50, 50, 40), (16, 16), 14)
                surface.blit(aura, (cx - 16, cy - 16))

            # Styled heart icon
            pygame.draw.circle(surface, color, (cx - 5, cy - 4), 7)
            pygame.draw.circle(surface, color, (cx + 5, cy - 4), 7)
            poly_pts = [(cx - 11, cy - 2), (cx + 11, cy - 2), (cx, cy + 11)]
            pygame.draw.polygon(surface, color, poly_pts)

        # ── Timer Badge (Below Header Bar) ──
        if timer_remaining is not None:
            t_sec = max(0, int(timer_remaining))
            t_col = Colors.RED if t_sec < 10 else Colors.YELLOW
            # Pulse effect when low on time
            pulse = 1.0
            if t_sec < 10:
                pulse = 1.0 + 0.15 * math.sin(pygame.time.get_ticks() / 150)

            t_surf = pygame.Surface((120, 36), pygame.SRCALPHA)
            pygame.draw.rect(t_surf, (20, 15, 35, 200), (0, 0, 120, 36), border_radius=18)
            pygame.draw.rect(t_surf, t_col, (0, 0, 120, 36), 2, border_radius=18)

            t_txt = self.font_medium.render(f"TIME  {t_sec}s", True, t_col)
            t_rect = t_txt.get_rect(center=(60, 18))
            t_surf.blit(t_txt, t_rect)

            surface.blit(t_surf, (SCREEN_WIDTH // 2 - 60, bar_y + bar_h + 10))

        # ── Combo Flares (Center Screen) ──
        if combo.show_display and combo.count >= 3:
            self._draw_combo(surface, combo)

        # ── Active Powerups Badges (Left Edge) ──
        active = powerup_sys.get_active_list()
        for idx, (ptype, remaining) in enumerate(active):
            self._draw_powerup_indicator(surface, ptype, remaining, idx)

        # ── Accuracy Badge (Bottom-Left) ──
        acc_bg = pygame.Surface((110, 26), pygame.SRCALPHA)
        pygame.draw.rect(acc_bg, (15, 20, 40, 160), (0, 0, 110, 26), border_radius=13)
        pygame.draw.rect(acc_bg, (80, 100, 140, 80), (0, 0, 110, 26), 1, border_radius=13)
        surface.blit(acc_bg, (20, surface.get_height() - 38))

        acc_txt = self.font_small.render(f"ACCURACY  {scoring.accuracy:.0f}%", True, (200, 210, 230))
        surface.blit(acc_txt, (30, surface.get_height() - 34))

    def _draw_combo(self, surface, combo):
        t = pygame.time.get_ticks() / 250
        scale = 1.0 + 0.08 * math.sin(t)
        size = max(36, int(64 * scale))
        try:
            f = pygame.font.Font(None, size)
        except Exception:
            f = self.font_combo

        combo_text = f"COMBO x{combo.count}"
        col = Colors.COMBO_FIRE if combo.count >= 5 else Colors.YELLOW
        txt = f.render(combo_text, True, col)
        rect = txt.get_rect(center=(SCREEN_WIDTH // 2, 150))

        # Glassmorphic banner behind combo
        glow = pygame.Surface((rect.width + 50, rect.height + 24), pygame.SRCALPHA)
        pygame.draw.rect(glow, (20, 10, 30, 210), glow.get_rect(), border_radius=16)
        pygame.draw.rect(glow, (*col, 180), glow.get_rect(), 2, border_radius=16)
        surface.blit(glow, (rect.x - 25, rect.y - 12))
        surface.blit(txt, rect)

        mult_txt = self.font_medium.render(f"+{int(combo.multiplier*100)}% SCORE BONUS", True, Colors.WHITE)
        mult_rect = mult_txt.get_rect(center=(SCREEN_WIDTH // 2, 192))
        surface.blit(mult_txt, mult_rect)

    def _draw_powerup_indicator(self, surface, ptype, remaining, idx):
        if ptype not in POWERUP_TYPES:
            return
        info = POWERUP_TYPES[ptype]
        y = 95 + idx * 42
        bar_w = 150
        bar_h = 32
        fill = max(0.0, min(1.0, remaining / info["duration"]))

        card = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        pygame.draw.rect(card, (20, 20, 45, 180), (0, 0, bar_w, bar_h), border_radius=16)
        # Progress gauge fill
        if fill > 0:
            pygame.draw.rect(card, (*info["color"], 140), (0, 0, int(bar_w * fill), bar_h), border_radius=16)
        pygame.draw.rect(card, info["color"], (0, 0, bar_w, bar_h), 2, border_radius=16)

        surface.blit(card, (20, y))

        label = self.font_small.render(f"{info['label']}", True, Colors.WHITE)
        surface.blit(label, (30, y + 6))


