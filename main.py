"""
Fruit Ninja AI — Gesture Controlled Edition
Main entry point.

Controls:
  • Move your index finger to slice fruits
  • Pinch to activate collected power-ups
  • Open palm to pause
  • Keyboard fallback: SPACE=pause, ESC=quit, M=menu, mouse=blade
"""
import sys
import os
import math
import time
import random

import pygame
import cv2
import numpy as np

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, Colors,
    GAME_MODES, FRUIT_TYPES, CAMERA_WIDTH, CAMERA_HEIGHT,
    BOSS_HP, BOSS_RADIUS, BOSS_SCORE, ACHIEVEMENTS,
)
from vision.camera import Camera
from vision.hand_detector import HandDetector
from vision.gesture_recognizer import GestureRecognizer, Gesture
from vision.motion_analyzer import MotionAnalyzer
from entities.fruit import Fruit
from entities.bomb import Bomb
from entities.powerup import PowerUp
from entities.blade import Blade
from entities.particle import ParticleSystem
from systems.fruit_spawner import FruitSpawner
from systems.scoring import ScoringSystem
from systems.combo import ComboSystem
from systems.lives import LivesSystem
from systems.powerup_system import PowerUpSystem
from systems.level_system import LevelSystem
from systems.achievement_system import AchievementSystem
from effects.screen_effects import ScreenEffects
from core.collision import blade_hits_entity
from ui.hud import HUD


# ═══════════════════════════════════════════════════════
#   GAME STATE
# ═══════════════════════════════════════════════════════
class GameState:
    MENU = "menu"
    MODE_SELECT = "mode_select"
    CALIBRATION = "calibration"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    ACHIEVEMENTS = "achievements_screen"
    BOSS = "boss"


# ═══════════════════════════════════════════════════════
#   BOSS
# ═══════════════════════════════════════════════════════
class BossEntity:
    """Mega Watermelon boss."""

    def __init__(self):
        self.hp = BOSS_HP
        self.max_hp = BOSS_HP
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.radius = BOSS_RADIUS
        self.phase = 0
        self.defeated = False
        self._angle = 0
        self._speed = 2

    def update(self):
        self._angle += self._speed
        self.x = SCREEN_WIDTH // 2 + int(math.cos(math.radians(self._angle)) * 200)
        self.y = SCREEN_HEIGHT // 2 + int(math.sin(math.radians(self._angle * 0.7)) * 100)
        # Speed up as HP decreases
        self._speed = 2 + (1 - self.hp / self.max_hp) * 5

    def hit(self):
        self.hp -= 1
        if self.hp <= 0:
            self.defeated = True

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        r = self.radius

        # Outer shell
        pygame.draw.circle(surface, (40, 160, 50), (cx, cy), r)
        # Dark stripes
        for i in range(6):
            angle = i * 60 + self._angle
            x1 = cx + int(math.cos(math.radians(angle)) * (r - 5))
            y1 = cy + int(math.sin(math.radians(angle)) * (r - 5))
            pygame.draw.line(surface, (30, 120, 35), (cx, cy), (x1, y1), 6)
        # Inner red
        pygame.draw.circle(surface, (200, 50, 50), (cx, cy), r - 12)
        # Seeds
        for i in range(8):
            a = i * 45 + self._angle * 0.5
            sx = cx + int(math.cos(math.radians(a)) * (r // 3))
            sy = cy + int(math.sin(math.radians(a)) * (r // 3))
            pygame.draw.ellipse(surface, (40, 30, 20), (sx - 3, sy - 5, 6, 10))

        # HP bar
        bar_w = 160
        bar_h = 14
        bx = cx - bar_w // 2
        by = cy - r - 25
        pygame.draw.rect(surface, (60, 60, 60), (bx, by, bar_w, bar_h), border_radius=4)
        fill = self.hp / self.max_hp
        fill_color = (50, 200, 80) if fill > 0.3 else (220, 50, 50)
        pygame.draw.rect(surface, fill_color, (bx, by, int(bar_w * fill), bar_h), border_radius=4)

        # Label
        font = pygame.font.Font(None, 28)
        txt = font.render("MEGA WATERMELON", True, Colors.WHITE)
        surface.blit(txt, txt.get_rect(center=(cx, by - 15)))


# ═══════════════════════════════════════════════════════
#   MAIN GAME CLASS
# ═══════════════════════════════════════════════════════
class FruitNinjaGame:
    """
    Top-level game class that owns all systems, runs the
    main loop, and handles state transitions.
    """

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        # ── Vision ──
        self.camera = Camera()
        self.hand_detector = HandDetector()
        self.gesture_recognizer = GestureRecognizer()
        self.motion_analyzer = MotionAnalyzer()

        # ── Entities ──
        self.blade = Blade()
        self.particles = ParticleSystem()
        self.fruits = []
        self.bombs = []
        self.powerups_entities = []

        # ── Systems ──
        self.spawner = FruitSpawner()
        self.scoring = ScoringSystem()
        self.combo = ComboSystem()
        self.lives = LivesSystem()
        self.powerup_sys = PowerUpSystem()
        self.level_sys = LevelSystem()
        self.achievements = AchievementSystem()

        # ── Effects ──
        self.screen_fx = ScreenEffects()

        # ── UI ──
        self.hud = HUD()
        self.font_title = pygame.font.Font(None, 72)
        self.font_large = pygame.font.Font(None, 52)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 26)
        self.font_popup = pygame.font.Font(None, 30)
        self.font_badge = pygame.font.Font(None, 20)


        # ── State ──
        self.state = GameState.MENU
        self.game_mode = "classic"
        self.running = True
        self.timer_start = 0
        self.timer_duration = None

        # ── Boss ──
        self.boss = None
        self._boss_last_hit = 0

        # ── Mouse fallback (for testing without camera) ──
        self.use_mouse = False
        self._mouse_trail = []

        # ── Menu animation ──
        self._menu_fruits = []
        for _ in range(12):
            self._menu_fruits.append({
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(0, SCREEN_HEIGHT),
                "r": random.randint(15, 35),
                "color": random.choice(list(FRUIT_TYPES.values()))["color"],
                "vx": random.uniform(-1, 1),
                "vy": random.uniform(-0.5, 0.5),
                "rot": random.uniform(0, 360),
                "rot_speed": random.uniform(-2, 2),
            })

        # Achievement popup queue
        self._achievement_popup = None
        self._achievement_popup_time = 0

        # Calibration
        self._calibration_start = 0
        self._hand_detected_frames = 0

        # Camera AR & Video state
        self.current_frame = None
        self.camera_mode = "ar_clear"  # "ar_clear", "ar_tint", "classic"
        self._open_palm_hold_frames = 0

    # ═══════════════════════════════════════════════════
    #   MAIN LOOP
    # ═══════════════════════════════════════════════════
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._render()
            pygame.display.flip()

        self._cleanup()

    # ───────────── Events ─────────────
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._on_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._on_click(event.pos)

    def _on_key(self, key):
        if key == pygame.K_ESCAPE:
            if self.state == GameState.PLAYING:
                self.state = GameState.PAUSED
            elif self.state == GameState.PAUSED:
                self.state = GameState.PLAYING
            elif self.state in (GameState.MENU, GameState.MODE_SELECT,
                                GameState.GAME_OVER, GameState.ACHIEVEMENTS):
                self.running = False
        elif key == pygame.K_SPACE:
            if self.state == GameState.PLAYING:
                self.state = GameState.PAUSED
            elif self.state == GameState.PAUSED:
                self.state = GameState.PLAYING
        elif key == pygame.K_m:
            if self.state in (GameState.GAME_OVER, GameState.PAUSED, GameState.ACHIEVEMENTS):
                self.state = GameState.MENU
        elif key == pygame.K_TAB:
            # Toggle mouse fallback
            self.use_mouse = not self.use_mouse
        elif key == pygame.K_r:
            if self.state == GameState.GAME_OVER:
                self._start_game(self.game_mode)
        elif key == pygame.K_c:
            modes = ["ar_clear", "ar_tint", "classic"]
            cur = modes.index(self.camera_mode) if self.camera_mode in modes else 0
            self.camera_mode = modes[(cur + 1) % len(modes)]

    def _on_click(self, pos):
        if self.state == GameState.MENU:
            self._handle_menu_click(pos)
        elif self.state == GameState.MODE_SELECT:
            self._handle_mode_select_click(pos)
        elif self.state == GameState.GAME_OVER:
            self._handle_game_over_click(pos)
        elif self.state == GameState.ACHIEVEMENTS:
            self._handle_achievements_click(pos)
        elif self.state == GameState.CALIBRATION:
            # Skip calibration
            self._start_game(self.game_mode)

    # ───────────── Update ─────────────
    def _update(self, dt):
        # Capture camera frame once per game tick to maximize performance and frame sync
        if not self.use_mouse and self.camera.is_ready:
            self.current_frame = self.camera.read()
        else:
            self.current_frame = None

        # Achievement popups
        self._update_achievement_popup()

        if self.state == GameState.MENU:
            self._update_menu()
        elif self.state == GameState.CALIBRATION:
            self._update_calibration()
        elif self.state == GameState.PLAYING:
            self._update_game(dt)
        elif self.state == GameState.BOSS:
            self._update_boss(dt)
        elif self.state == GameState.PAUSED:
            pass

    def _update_menu(self):
        for f in self._menu_fruits:
            f["x"] += f["vx"]
            f["y"] += f["vy"]
            f["rot"] += f["rot_speed"]
            if f["x"] < -50:
                f["x"] = SCREEN_WIDTH + 50
            elif f["x"] > SCREEN_WIDTH + 50:
                f["x"] = -50
            if f["y"] < -50:
                f["y"] = SCREEN_HEIGHT + 50
            elif f["y"] > SCREEN_HEIGHT + 50:
                f["y"] = -50

    def _update_calibration(self):
        frame = self.current_frame
        if frame is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            hands = self.hand_detector.detect(rgb)
            if hands:
                self._hand_detected_frames += 1
            else:
                self._hand_detected_frames = max(0, self._hand_detected_frames - 1)

        # Auto-start after 2 seconds of stable detection or 5s total
        elapsed = time.time() - self._calibration_start
        if self._hand_detected_frames > 40 or elapsed > 5:
            self._start_game(self.game_mode)

    def _update_game(self, dt):
        # ── Timer check ──
        if self.timer_duration is not None:
            elapsed = time.time() - self.timer_start
            if elapsed >= self.timer_duration:
                self._game_over()
                return

        # ── Vision pipeline ──
        hand_pos = self._get_hand_position()

        # ── Power-up time scale ──
        time_scale = self.powerup_sys.time_scale

        # ── Update motion analyzer ──
        self.motion_analyzer.update(hand_pos)

        # ── Blade fire mode ──
        self.blade.fire_mode = self.powerup_sys.fire_blade_active

        # ── Spawner ──
        mode_info = GAME_MODES[self.game_mode]
        diff = self.level_sys.get_difficulty()
        self.spawner.configure(
            diff["spawn_rate"], diff["max_fruits"],
            diff["bomb_chance"] if mode_info["bombs"] else 0.0,
            diff["speed_mult"],
        )
        new_fruits, new_bombs, new_powerups = self.spawner.update(
            len(self.fruits) + len(self.bombs)
        )
        self.fruits.extend(new_fruits)
        self.bombs.extend(new_bombs)
        self.powerups_entities.extend(new_powerups)

        # ── Update entities ──
        for f in self.fruits:
            f.update(time_scale)
        for b in self.bombs:
            b.update(time_scale)
        for p in self.powerups_entities:
            p.update(time_scale)

        # ── Collision detection ──
        if self.motion_analyzer.is_slicing or (self.use_mouse and pygame.mouse.get_pressed()[0]):
            segments = self.motion_analyzer.get_blade_segments()
            if not segments and self.use_mouse and pygame.mouse.get_pressed()[0]:
                mpos = pygame.mouse.get_pos()
                segments = [(mpos, mpos)]
            self._check_collisions(segments)

        # ── Missed fruits ──
        for f in self.fruits:
            if f.missed and not f.sliced and not getattr(f, '_counted_miss', False):
                self.scoring.fruit_missed()
                f._counted_miss = True

        # ── Prune dead entities ──
        self.fruits = [f for f in self.fruits if f.alive]
        self.bombs = [b for b in self.bombs if b.alive]
        self.powerups_entities = [p for p in self.powerups_entities if p.alive]

        # ── Systems update ──
        self.combo.update()
        self.lives.update()
        self.powerup_sys.update()
        self.level_sys.update(self.scoring.score)
        self.particles.update()
        self.screen_fx.update()

        # ── Achievements ──
        self.achievements.check_conditions(
            self.scoring, self.combo, self.level_sys, self.game_mode
        )
        pending = self.achievements.pop_pending()
        if pending:
            aid = pending[0]
            info = ACHIEVEMENTS.get(aid, {})
            self._achievement_popup = info.get("name", aid)
            self._achievement_popup_time = time.time()

        # ── Level up effect ──
        if self.level_sys.leveled_up:
            self.particles.add_popup(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50,
                f"LEVEL {self.level_sys.level}!",
                Colors.CYAN, 48
            )
            # Check for boss
            if self.level_sys.is_boss_level:
                self._enter_boss()

        # ── Death check ──
        if not self.lives.is_alive:
            self._game_over()

    def _update_boss(self, dt):
        if self.boss is None:
            return

        hand_pos = self._get_hand_position()
        self.motion_analyzer.update(hand_pos)

        self.boss.update()
        self.particles.update()
        self.screen_fx.update()

        # Collision with boss
        now = time.time()
        if self.motion_analyzer.is_slicing and now - self._boss_last_hit > 0.3:
            segments = self.motion_analyzer.get_blade_segments()
            if blade_hits_entity(segments, self.boss.x, self.boss.y, self.boss.radius):
                self.boss.hit()
                self._boss_last_hit = now
                self.particles.emit_juice(
                    int(self.boss.x), int(self.boss.y),
                    (200, 50, 50), 20
                )
                self.screen_fx.trigger_shake(6)
                self.particles.add_popup(
                    self.boss.x, self.boss.y - 60,
                    f"HIT! {self.boss.hp}/{self.boss.max_hp}",
                    Colors.RED, 32
                )

        if self.boss.defeated:
            self.scoring.add_score(BOSS_SCORE)
            self.achievements.unlock("boss_slayer")
            self.particles.emit_explosion(int(self.boss.x), int(self.boss.y), 40)
            self.particles.add_popup(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                f"BOSS DEFEATED! +{BOSS_SCORE}",
                Colors.GOLD, 48
            )
            self.boss = None
            self.state = GameState.PLAYING

    def _get_hand_position(self):
        """Get index fingertip position from camera or mouse with moving average smoothing."""
        if self.use_mouse:
            mx, my = pygame.mouse.get_pos()
            if pygame.mouse.get_pressed()[0]:
                return self.hand_detector.smooth_position((mx, my))
            return self.hand_detector.smooth_position(None)

        frame = self.current_frame
        if frame is None:
            return self.hand_detector.smooth_position(None)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hands = self.hand_detector.detect(rgb)
        if not hands:
            self._open_palm_hold_frames = 0
            return self.hand_detector.smooth_position(None)

        hand = hands[0]
        lm = hand["landmarks"]
        screen_pts = self.hand_detector.to_screen(
            lm, SCREEN_WIDTH, SCREEN_HEIGHT,
            cam_w=self.camera.width, cam_h=self.camera.height
        )
        index_tip = screen_pts[HandDetector.INDEX_TIP]

        # Gesture detection: require deliberate steady open palm to pause (no accidental pause during fast slices)
        gesture, meta = self.gesture_recognizer.recognize(lm)
        if gesture == Gesture.OPEN_PALM and self.state == GameState.PLAYING:
            if not self.motion_analyzer.is_slicing and self.motion_analyzer.speed < 200:
                self._open_palm_hold_frames += 1
                if self._open_palm_hold_frames > 15:
                    self.state = GameState.PAUSED
                    self._open_palm_hold_frames = 0
            else:
                self._open_palm_hold_frames = 0
        else:
            self._open_palm_hold_frames = 0

        raw_pos = (int(index_tip[0]), int(index_tip[1]))
        return self.hand_detector.smooth_position(raw_pos)


    def _check_collisions(self, segments):
        """Test blade segments against all entities."""
        # Fruits
        for fruit in self.fruits:
            if fruit.sliced or fruit.missed:
                continue
            if blade_hits_entity(segments, fruit.x, fruit.y, fruit.radius):
                fruit.slice()
                self.combo.register_slice()
                mult = self.combo.multiplier * self.powerup_sys.score_multiplier
                gained = self.scoring.add_score(fruit.points, mult)
                self.scoring.fruit_sliced()
                # Effects
                self.particles.emit_juice(
                    int(fruit.x), int(fruit.y), fruit.juice_color
                )
                self.particles.add_popup(
                    fruit.x, fruit.y - 30,
                    f"+{gained}",
                    Colors.YELLOW if mult > 1 else Colors.WHITE,
                    32 if mult > 1 else 26,
                )
                if self.combo.count >= 3:
                    self.particles.emit_sparkle(int(fruit.x), int(fruit.y))

        # Bombs
        for bomb in self.bombs:
            if bomb.hit:
                continue
            if blade_hits_entity(segments, bomb.x, bomb.y, bomb.radius):
                bomb.trigger()
                self.scoring.bomb_hit()
                self.combo.count = 0
                # Effects
                self.particles.emit_explosion(int(bomb.x), int(bomb.y))
                self.screen_fx.trigger_shake(15 if bomb.type == "mega" else 10)
                self.screen_fx.trigger_flash((255, 0, 0), 80)
                if self.game_mode in ["classic", "survival"]:
                    self.lives.lose(self.lives.lives)
                    self._game_over()
                    break
                else:
                    self.lives.lose(bomb.lives_cost)
                    if not self.lives.is_alive:
                        self._game_over()
                        break

        # Powerups
        for pu in self.powerups_entities:
            if pu.collected:
                continue
            if blade_hits_entity(segments, pu.x, pu.y, pu.radius):
                pu.collect()
                self.powerup_sys.activate(pu.type, pu.duration)
                self.particles.emit_sparkle(
                    int(pu.x), int(pu.y), pu.color, 12
                )
                self.particles.add_popup(
                    pu.x, pu.y - 30, pu.label, pu.color, 32
                )

    # ───────────── State transitions ─────────────
    def _start_game(self, mode):
        self.game_mode = mode
        mode_info = GAME_MODES[mode]
        self.state = GameState.PLAYING
        self.fruits.clear()
        self.bombs.clear()
        self.powerups_entities.clear()
        self.particles.clear()
        self.motion_analyzer.clear()
        self.scoring.reset()
        self.combo.reset()
        self.lives.reset(mode_info["lives"])
        self.powerup_sys.reset()
        self.level_sys.reset()
        self.spawner = FruitSpawner()
        self.boss = None
        if mode_info["timer"] is not None:
            self.timer_start = time.time()
            self.timer_duration = mode_info["timer"]
        else:
            self.timer_start = 0
            self.timer_duration = None

    def _game_over(self):
        self.state = GameState.GAME_OVER
        self.scoring.finalize()

    def _enter_boss(self):
        self.state = GameState.BOSS
        self.boss = BossEntity()
        self.fruits.clear()
        self.bombs.clear()

    def _update_achievement_popup(self):
        if self._achievement_popup and time.time() - self._achievement_popup_time > 3:
            self._achievement_popup = None

    # ═══════════════════════════════════════════════════
    #   RENDERING
    # ═══════════════════════════════════════════════════
    def _render(self):
        if self.state == GameState.MENU:
            self._render_menu()
        elif self.state == GameState.MODE_SELECT:
            self._render_mode_select()
        elif self.state == GameState.CALIBRATION:
            self._render_calibration()
        elif self.state == GameState.PLAYING:
            self._render_game()
        elif self.state == GameState.BOSS:
            self._render_boss()
        elif self.state == GameState.PAUSED:
            self._render_pause()
        elif self.state == GameState.GAME_OVER:
            self._render_game_over()
        elif self.state == GameState.ACHIEVEMENTS:
            self._render_achievements()

        # Achievement popup overlay
        if self._achievement_popup:
            self._render_achievement_popup()

    # ─── Background helpers ───
    def _draw_gradient_bg(self, surface, top_color, bot_color):
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(top_color[0] + (bot_color[0] - top_color[0]) * t)
            g = int(top_color[1] + (bot_color[1] - top_color[1]) * t)
            b = int(top_color[2] + (bot_color[2] - top_color[2]) * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    def _draw_game_bg(self):
        """Dark gradient with subtle grid."""
        self._draw_gradient_bg(self.screen, (10, 10, 35), (5, 5, 20))
        # Subtle grid
        grid_color = (20, 20, 45)
        for x in range(0, SCREEN_WIDTH, 60):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 60):
            pygame.draw.line(self.screen, grid_color, (0, y), (SCREEN_WIDTH, y))

    # ─── Menu ───
    def _render_menu(self):
        self._draw_gradient_bg(self.screen, (8, 8, 25), (28, 12, 55))

        # Floating fruit decorations with halo glow
        for f in self._menu_fruits:
            cx, cy = int(f["x"]), int(f["y"])
            r = f["r"]
            # Outer glow
            halo = pygame.Surface((r * 3, r * 3), pygame.SRCALPHA)
            pygame.draw.circle(halo, (*f["color"], 40), (r * 3 // 2, r * 3 // 2), r * 3 // 2)
            self.screen.blit(halo, (cx - r * 3 // 2, cy - r * 3 // 2))

            pygame.draw.circle(self.screen, f["color"], (cx, cy), r)
            highlight = tuple(min(c + 60, 255) for c in f["color"])
            pygame.draw.circle(self.screen, highlight, (cx - r // 3, cy - r // 3), r // 3)

        # Floating Title Banner
        t = pygame.time.get_ticks() / 1000
        title_y = 135 + int(math.sin(t * 2.5) * 6)

        # Glassmorphic Title Plate
        plate_w, plate_h = 480, 85
        plate = pygame.Surface((plate_w, plate_h), pygame.SRCALPHA)
        pygame.draw.rect(plate, (15, 18, 45, 180), (0, 0, plate_w, plate_h), border_radius=20)
        pygame.draw.rect(plate, (120, 100, 255, 120), (0, 0, plate_w, plate_h), 2, border_radius=20)
        pygame.draw.line(plate, (255, 255, 255, 50), (20, 2), (plate_w - 20, 2), width=1)
        self.screen.blit(plate, (SCREEN_WIDTH // 2 - plate_w // 2, title_y - 30))

        # Title text with drop-shadow glow
        shadow_txt = self.font_title.render("FRUIT NINJA", True, (80, 30, 150))
        title_txt = self.font_title.render("FRUIT NINJA", True, Colors.WHITE)
        title_rect = title_txt.get_rect(center=(SCREEN_WIDTH // 2, title_y + 12))

        self.screen.blit(shadow_txt, (title_rect.x + 3, title_rect.y + 3))
        self.screen.blit(title_txt, title_rect)

        # Glassmorphic Menu Buttons
        buttons = [
            ("PLAY", Colors.GREEN),
            ("GAME MODES", Colors.BLUE),
            ("ACHIEVEMENTS", Colors.GOLD),
            ("EXIT", Colors.RED),
        ]
        self._menu_buttons = []
        start_y = 275
        mx, my = pygame.mouse.get_pos()

        for i, (label, color) in enumerate(buttons):
            by = start_y + i * 68
            btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 170, by, 340, 54)
            self._menu_buttons.append((btn_rect, label))

            hovered = btn_rect.collidepoint(mx, my)

            btn_surf = pygame.Surface((340, 54), pygame.SRCALPHA)
            bg_alpha = 210 if hovered else 140
            pygame.draw.rect(btn_surf, (20, 25, 55, bg_alpha), (0, 0, 340, 54), border_radius=16)

            # Hover neon glow border
            border_col = tuple(min(c + 40, 255) for c in color) if hovered else color
            pygame.draw.rect(btn_surf, border_col, (0, 0, 340, 54), 2 if not hovered else 3, border_radius=16)

            if hovered:
                # Top sheen line
                pygame.draw.line(btn_surf, (255, 255, 255, 60), (16, 2), (324, 2), width=1)

            self.screen.blit(btn_surf, btn_rect.topleft)

            txt = self.font_medium.render(label, True, Colors.WHITE)
            self.screen.blit(txt, txt.get_rect(center=btn_rect.center))

        # Bottom Glass Status Bar
        status_bar = pygame.Surface((SCREEN_WIDTH - 40, 44), pygame.SRCALPHA)
        pygame.draw.rect(status_bar, (12, 14, 35, 180), (0, 0, SCREEN_WIDTH - 40, 44), border_radius=14)
        pygame.draw.rect(status_bar, (80, 100, 160, 60), (0, 0, SCREEN_WIDTH - 40, 44), 1, border_radius=14)
        self.screen.blit(status_bar, (20, SCREEN_HEIGHT - 54))

        cam_status = "CAMERA: READY" if self.camera.is_ready else "CAMERA: NOT FOUND"
        cam_col = Colors.GREEN if self.camera.is_ready else Colors.RED
        cam_txt = self.font_small.render(cam_status, True, cam_col)
        self.screen.blit(cam_txt, (35, SCREEN_HEIGHT - 42))

        hint = self.font_small.render(f"TAB: Mouse  •  C: Cam Mode ({self.camera_mode.upper()})", True, (160, 170, 210))
        self.screen.blit(hint, (260, SCREEN_HEIGHT - 42))

        mode_txt = self.font_small.render(
            "MOUSE MODE" if self.use_mouse else "HAND TRACKING",
            True, Colors.YELLOW if self.use_mouse else Colors.CYAN
        )
        self.screen.blit(mode_txt, mode_txt.get_rect(bottomright=(SCREEN_WIDTH - 35, SCREEN_HEIGHT - 22)))


    def _handle_menu_click(self, pos):
        if not hasattr(self, '_menu_buttons'):
            return
        for rect, label in self._menu_buttons:
            if rect.collidepoint(pos):
                if "PLAY" in label:
                    if self.use_mouse:
                        self._start_game("classic")
                    else:
                        self.state = GameState.CALIBRATION
                        self._calibration_start = time.time()
                        self._hand_detected_frames = 0
                elif "GAME MODES" in label:
                    self.state = GameState.MODE_SELECT
                elif "ACHIEVEMENTS" in label:
                    self.state = GameState.ACHIEVEMENTS
                elif "EXIT" in label:
                    self.running = False

    # ─── Mode Select ───
    def _render_mode_select(self):
        self._draw_gradient_bg(self.screen, (8, 12, 35), (20, 10, 45))

        # Title
        title = self.font_large.render("SELECT GAME MODE", True, Colors.WHITE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 50)))

        sub = self.font_small.render("Choose your slicing challenge", True, (160, 170, 210))
        self.screen.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 82)))

        modes = list(GAME_MODES.items())
        descs = {
            "classic": "3 lives. Slice fruits & powerups, dodge bombs. Classic ninja test!",
            "arcade": "60-second high-speed blitz! Maximum fruits, special combos.",
            "zen": "Pure slicing relaxation. No bombs, no lives lost, just fruits.",
            "survival": "Hardcore test! Single mistake and game is over immediately.",
        }
        self._mode_buttons = []

        # 2x2 Grid Layout
        mx, my = pygame.mouse.get_pos()
        card_w, card_h = 560, 115

        for i, (mode_id, info) in enumerate(modes):
            col = i % 2
            row = i // 2
            bx = 50 + col * 620
            by = 135 + row * 140

            btn_rect = pygame.Rect(bx, by, card_w, card_h)
            self._mode_buttons.append((btn_rect, mode_id))

            hovered = btn_rect.collidepoint(mx, my)

            surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            bg_alpha = 210 if hovered else 140
            pygame.draw.rect(surf, (20, 24, 55, bg_alpha), (0, 0, card_w, card_h), border_radius=18)

            border = Colors.CYAN if hovered else (70, 80, 130)
            pygame.draw.rect(surf, border, (0, 0, card_w, card_h), 2 if not hovered else 3, border_radius=18)
            if hovered:
                pygame.draw.line(surf, (255, 255, 255, 50), (16, 2), (card_w - 16, 2), width=1)

            self.screen.blit(surf, btn_rect.topleft)

            # Title
            header_txt = self.font_large.render(f"{info['label'].upper()}", True, Colors.WHITE)
            self.screen.blit(header_txt, (btn_rect.x + 22, btn_rect.y + 14))

            # Description
            desc_txt = self.font_small.render(descs.get(mode_id, ""), True, (180, 190, 220))
            self.screen.blit(desc_txt, (btn_rect.x + 22, btn_rect.y + 54))

            # Feature Pill Tags
            tag_parts = []
            if info["lives"] < 99:
                tag_parts.append(f"{info['lives']} Lives")
            if info["timer"]:
                tag_parts.append(f"{info['timer']}s Timer")
            if not info["bombs"]:
                tag_parts.append("No Bombs")
            else:
                tag_parts.append("Bombs Active")

            tag_str = "   •   ".join(tag_parts)
            tag_txt = self.font_badge.render(tag_str, True, Colors.CYAN if hovered else (140, 160, 200))
            self.screen.blit(tag_txt, (btn_rect.x + 22, btn_rect.y + 86))


        # Back hint
        back_bar = pygame.Surface((140, 36), pygame.SRCALPHA)
        pygame.draw.rect(back_bar, (20, 25, 55, 180), (0, 0, 140, 36), border_radius=12)
        pygame.draw.rect(back_bar, (80, 100, 160, 80), (0, 0, 140, 36), 1, border_radius=12)
        self.screen.blit(back_bar, (20, SCREEN_HEIGHT - 48))

        back = self.font_small.render("ESC  Back", True, (200, 210, 240))
        self.screen.blit(back, (35, SCREEN_HEIGHT - 40))

    def _handle_mode_select_click(self, pos):
        if not hasattr(self, '_mode_buttons'):
            return
        for rect, mode_id in self._mode_buttons:
            if rect.collidepoint(pos):
                self.game_mode = mode_id
                if self.use_mouse:
                    self._start_game(mode_id)
                else:
                    self.state = GameState.CALIBRATION
                    self._calibration_start = time.time()
                    self._hand_detected_frames = 0

    # ─── Calibration ───
    def _render_calibration(self):
        self._draw_gradient_bg(self.screen, (8, 8, 25), (5, 5, 20))

        title = self.font_large.render("CAMERA CALIBRATION", True, Colors.WHITE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 45)))

        frame = self.current_frame
        if frame is not None:
            preview_w, preview_h = 480, 360
            frame_resized = cv2.resize(frame, (preview_w, preview_h))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            surf = pygame.image.frombuffer(frame_rgb.tobytes(), (preview_w, preview_h), 'RGB')
            px = SCREEN_WIDTH // 2 - preview_w // 2
            py = 90
            self.screen.blit(surf, (px, py))

            border_col = Colors.GREEN if self._hand_detected_frames > 20 else Colors.RED
            pygame.draw.rect(self.screen, border_col, (px - 3, py - 3, preview_w + 6, preview_h + 6), 3, border_radius=8)

        instructions = [
            "Center your hand inside camera view",
            "Keep index finger extended for blade tracking",
            "Move hand around screen to slice fruits",
        ]
        for i, line in enumerate(instructions):
            txt = self.font_small.render(line, True, (190, 190, 220))
            self.screen.blit(txt, txt.get_rect(center=(SCREEN_WIDTH // 2, 475 + i * 26)))

        if self._hand_detected_frames > 20:
            status = self.font_medium.render("Hand Detected - Ready!", True, Colors.GREEN)
        else:
            status = self.font_medium.render("Searching for hand...", True, Colors.YELLOW)
        self.screen.blit(status, status.get_rect(center=(SCREEN_WIDTH // 2, 565)))

        elapsed = time.time() - self._calibration_start
        progress = min(1.0, elapsed / 5.0)
        bar_w = 320
        bar_h = 8
        bx = SCREEN_WIDTH // 2 - bar_w // 2
        by = 600
        pygame.draw.rect(self.screen, (30, 35, 60), (bx, by, bar_w, bar_h), border_radius=4)
        pygame.draw.rect(self.screen, Colors.CYAN, (bx, by, int(bar_w * progress), bar_h), border_radius=4)

        skip = self.font_small.render("Click anywhere to start immediately", True, (150, 160, 200))
        self.screen.blit(skip, skip.get_rect(center=(SCREEN_WIDTH // 2, 638)))

    # ─── Game ───
    def _render_game(self):
        if not self.use_mouse and self.camera.is_ready and self.current_frame is not None:
            if self.camera_mode == "classic":
                self._draw_game_bg()
                self._draw_camera_feed()
            else:
                self._draw_camera_background()
        else:
            self._draw_game_bg()

        offset = self.screen_fx.get_offset()

        for fruit in self.fruits:
            fruit.draw(self.screen)
        for bomb in self.bombs:
            bomb.draw(self.screen)
        for pu in self.powerups_entities:
            pu.draw(self.screen)

        trail = self.motion_analyzer.get_trail_points()
        self.blade.draw(self.screen, trail, self.motion_analyzer.is_slicing)

        self.particles.draw(self.screen, self.font_popup)
        self.screen_fx.draw_flash(self.screen)

        if self.powerup_sys.freeze_active or self.powerup_sys.slow_motion_active:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((100, 150, 255, 20) if self.powerup_sys.freeze_active else (150, 80, 255, 15))
            self.screen.blit(overlay, (0, 0))

        timer_remaining = None
        if self.timer_duration is not None:
            timer_remaining = max(0, self.timer_duration - (time.time() - self.timer_start))
        self.hud.draw(
            self.screen, self.scoring, self.lives, self.combo,
            self.level_sys, self.powerup_sys, timer_remaining
        )

    def _draw_camera_background(self):
        """
        Renders the live webcam feed across the entire game screen.
        Applies a center-crop to 16:9 so the image is never distorted,
        followed by a stylish AR gaming vignette / cyber tint.
        """
        frame = self.current_frame
        if frame is None:
            self._draw_game_bg()
            return

        h, w = frame.shape[:2]
        target_aspect = SCREEN_WIDTH / SCREEN_HEIGHT
        aspect = w / h

        if aspect < target_aspect:
            crop_h = int(w / target_aspect)
            y0 = (h - crop_h) // 2
            cropped = frame[y0:y0 + crop_h, :]
        else:
            crop_w = int(h * target_aspect)
            x0 = (w - crop_w) // 2
            cropped = frame[:, x0:x0 + crop_w]

        resized = cv2.resize(cropped, (SCREEN_WIDTH, SCREEN_HEIGHT), interpolation=cv2.INTER_LINEAR)
        frame_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        cam_surf = pygame.image.frombuffer(frame_rgb.tobytes(), (SCREEN_WIDTH, SCREEN_HEIGHT), 'RGB')
        self.screen.blit(cam_surf, (0, 0))

        if self.camera_mode == "ar_tint":
            tint_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            tint_overlay.fill((10, 15, 40, 95))
            self.screen.blit(tint_overlay, (0, 0))
            # Subtle futuristic cyber grid
            grid_col = (100, 150, 255, 25)
            grid_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for x in range(0, SCREEN_WIDTH, 80):
                pygame.draw.line(grid_surf, grid_col, (x, 0), (x, SCREEN_HEIGHT))
            for y in range(0, SCREEN_HEIGHT, 80):
                pygame.draw.line(grid_surf, grid_col, (0, y), (SCREEN_WIDTH, y))
            self.screen.blit(grid_surf, (0, 0))
        else:
            # "ar_clear": Sleek glassmorphic gradient top/bottom vignette to enhance HUD contrast
            vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(vignette, (8, 12, 28, 85), (0, 0, SCREEN_WIDTH, 82))
            pygame.draw.rect(vignette, (8, 12, 28, 85), (0, SCREEN_HEIGHT - 55, SCREEN_WIDTH, 55))
            self.screen.blit(vignette, (0, 0))

    def _draw_camera_feed(self):
        """Small camera preview in bottom-right corner (for classic mode)."""
        frame = self.current_frame
        if frame is None:
            return
        preview_w, preview_h = 160, 120
        frame_resized = cv2.resize(frame, (preview_w, preview_h))
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        surf = pygame.image.frombuffer(frame_rgb.tobytes(), (preview_w, preview_h), 'RGB')
        x = SCREEN_WIDTH - preview_w - 15
        y = SCREEN_HEIGHT - preview_h - 15

        bg = pygame.Surface((preview_w + 8, preview_h + 8), pygame.SRCALPHA)
        pygame.draw.rect(bg, (10, 15, 35, 180), (0, 0, preview_w + 8, preview_h + 8), border_radius=10)
        pygame.draw.rect(bg, (100, 150, 255, 100), (0, 0, preview_w + 8, preview_h + 8), 1, border_radius=10)
        self.screen.blit(bg, (x - 4, y - 4))
        self.screen.blit(surf, (x, y))

    # ─── Boss ───
    def _render_boss(self):
        if not self.use_mouse and self.camera.is_ready and self.current_frame is not None:
            if self.camera_mode == "classic":
                self._draw_game_bg()
                self._draw_camera_feed()
            else:
                self._draw_camera_background()
        else:
            self._draw_game_bg()

        t = pygame.time.get_ticks() / 500
        if int(t) % 2 == 0:
            warn_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            warn_overlay.fill((200, 30, 30, 20))
            self.screen.blit(warn_overlay, (0, 0))

        if self.boss:
            self.boss.draw(self.screen)

        trail = self.motion_analyzer.get_trail_points()
        self.blade.draw(self.screen, trail, self.motion_analyzer.is_slicing)

        self.particles.draw(self.screen, self.font_popup)
        self.screen_fx.draw_flash(self.screen)

        label = self.font_large.render("MEGA WATERMELON BOSS", True, Colors.RED)
        self.screen.blit(label, label.get_rect(center=(SCREEN_WIDTH // 2, 35)))

    # ─── Pause ───
    def _render_pause(self):
        self._render_game()

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 5, 15, 185))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 440, 320
        px = SCREEN_WIDTH // 2 - panel_w // 2
        py = SCREEN_HEIGHT // 2 - panel_h // 2
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (18, 22, 50, 220), (0, 0, panel_w, panel_h), border_radius=20)
        pygame.draw.rect(panel, Colors.CYAN, (0, 0, panel_w, panel_h), 2, border_radius=20)
        self.screen.blit(panel, (px, py))

        title = self.font_large.render("GAME PAUSED", True, Colors.WHITE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, py + 45)))

        hints = [
            "SPACE / ESC   —   Resume Game",
            "M   —   Return to Main Menu",
            "TAB   —   Toggle Mouse Control",
            f"C   —   Camera Mode: {self.camera_mode.upper()}",
        ]
        for i, h in enumerate(hints):
            txt = self.font_small.render(h, True, (190, 200, 230))
            self.screen.blit(txt, txt.get_rect(center=(SCREEN_WIDTH // 2, py + 120 + i * 36)))

    # ─── Game Over ───
    def _render_game_over(self):
        self._draw_gradient_bg(self.screen, (15, 6, 20), (8, 4, 18))

        panel_w, panel_h = 540, 540
        px = SCREEN_WIDTH // 2 - panel_w // 2
        py = SCREEN_HEIGHT // 2 - panel_h // 2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, (18, 20, 50, 220), (0, 0, panel_w, panel_h), border_radius=22)
        border_col = Colors.GOLD if self.scoring.is_new_high else Colors.PURPLE
        pygame.draw.rect(panel, border_col, (0, 0, panel_w, panel_h), 2, border_radius=22)
        pygame.draw.line(panel, (255, 255, 255, 40), (20, 2), (panel_w - 20, 2), width=1)
        self.screen.blit(panel, (px, py))

        # Title
        title_str = "NEW HIGH SCORE!" if self.scoring.is_new_high else "GAME OVER"
        title_col = Colors.GOLD if self.scoring.is_new_high else Colors.RED
        title = self.font_large.render(title_str, True, title_col)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, py + 40)))

        # Score display
        score_txt = self.font_title.render(f"{self.scoring.score:,}", True, Colors.WHITE)
        self.screen.blit(score_txt, score_txt.get_rect(center=(SCREEN_WIDTH // 2, py + 100)))

        # Performance Grade/Rank Badge
        score = self.scoring.score
        acc = self.scoring.accuracy
        if score >= 1000 and acc >= 80:
            rank_str, rank_col = "S-RANK", Colors.GOLD
        elif score >= 500:
            rank_str, rank_col = "A-RANK", Colors.CYAN
        elif score >= 200:
            rank_str, rank_col = "B-RANK", Colors.GREEN
        else:
            rank_str, rank_col = "C-RANK", (180, 180, 200)

        rank_badge = pygame.Surface((130, 28), pygame.SRCALPHA)
        pygame.draw.rect(rank_badge, (*rank_col, 40), (0, 0, 130, 28), border_radius=14)
        pygame.draw.rect(rank_badge, rank_col, (0, 0, 130, 28), 1, border_radius=14)
        self.screen.blit(rank_badge, (SCREEN_WIDTH // 2 - 65, py + 140))

        rank_txt = self.font_small.render(rank_str, True, rank_col)
        self.screen.blit(rank_txt, rank_txt.get_rect(center=(SCREEN_WIDTH // 2, py + 154)))

        # Stats Grid
        stats = [
            ("Fruits Sliced", f"{self.scoring.fruits_sliced}"),
            ("Bombs Hit", f"{self.scoring.bombs_hit}"),
            ("Max Combo", f"x{self.combo.max_combo}"),
            ("Accuracy", f"{self.scoring.accuracy:.0f}%"),
            ("Level Reached", f"Level {self.level_sys.level}"),
        ]
        sy = py + 195
        for label, value in stats:
            pygame.draw.line(self.screen, (35, 40, 70), (px + 35, sy + 30), (px + panel_w - 35, sy + 30))
            l_txt = self.font_medium.render(label, True, (180, 190, 220))
            v_txt = self.font_medium.render(value, True, Colors.WHITE)
            self.screen.blit(l_txt, (px + 40, sy + 2))
            self.screen.blit(v_txt, v_txt.get_rect(right=px + panel_w - 40, top=sy + 2))
            sy += 42

        # Action Buttons
        btn_y = py + panel_h - 75
        self._go_play_rect = pygame.Rect(SCREEN_WIDTH // 2 - 215, btn_y, 200, 48)
        self._go_menu_rect = pygame.Rect(SCREEN_WIDTH // 2 + 15, btn_y, 200, 48)

        mx, my = pygame.mouse.get_pos()
        for rect, label, color in [
            (self._go_play_rect, "PLAY AGAIN", Colors.GREEN),
            (self._go_menu_rect, "MAIN MENU", Colors.BLUE),
        ]:
            hovered = rect.collidepoint(mx, my)
            btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            bg_alpha = 210 if hovered else 140
            pygame.draw.rect(btn_surf, (20, 25, 55, bg_alpha), (0, 0, rect.width, rect.height), border_radius=14)
            pygame.draw.rect(btn_surf, color, (0, 0, rect.width, rect.height), 2, border_radius=14)
            self.screen.blit(btn_surf, rect.topleft)


            txt = self.font_medium.render(label, True, Colors.WHITE)
            self.screen.blit(txt, txt.get_rect(center=rect.center))

    def _handle_game_over_click(self, pos):
        if hasattr(self, '_go_play_rect') and self._go_play_rect.collidepoint(pos):
            self._start_game(self.game_mode)
        elif hasattr(self, '_go_menu_rect') and self._go_menu_rect.collidepoint(pos):
            self.state = GameState.MENU

    # ─── Achievements Screen ───
    def _render_achievements(self):
        self._draw_gradient_bg(self.screen, (10, 8, 28), (20, 10, 45))

        title = self.font_large.render("ACHIEVEMENTS", True, Colors.GOLD)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 40)))

        all_ach = self.achievements.get_all()
        unlocked_count = sum(1 for _, _, u in all_ach if u)
        counter = self.font_small.render(
            f"Unlocked: {unlocked_count} / {len(all_ach)}", True, Colors.CYAN
        )
        self.screen.blit(counter, counter.get_rect(center=(SCREEN_WIDTH // 2, 75)))

        self._ach_back_rect = pygame.Rect(20, SCREEN_HEIGHT - 48, 130, 36)

        for i, (aid, info, unlocked) in enumerate(all_ach):
            row = i % 5
            col = i // 5
            bx = 60 + col * (SCREEN_WIDTH // 2 - 20)
            by = 105 + row * 102

            card_w, card_h = SCREEN_WIDTH // 2 - 70, 88
            card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            bg_col = (25, 32, 65, 200) if unlocked else (18, 20, 45, 120)
            pygame.draw.rect(card, bg_col, (0, 0, card_w, card_h), border_radius=16)
            border = Colors.GOLD if unlocked else (60, 65, 95)
            pygame.draw.rect(card, border, (0, 0, card_w, card_h), 2 if unlocked else 1, border_radius=16)
            self.screen.blit(card, (bx, by))

            name_col = Colors.GOLD if unlocked else (130, 140, 170)
            name = self.font_medium.render(info["name"], True, name_col)
            self.screen.blit(name, (bx + 16, by + 14))

            desc = self.font_small.render(info["desc"], True, (180, 190, 220))
            self.screen.blit(desc, (bx + 16, by + 50))

            status_str = "UNLOCKED" if unlocked else "LOCKED"
            status_col = Colors.GREEN if unlocked else (100, 110, 140)
            st_txt = self.font_badge.render(status_str, True, status_col)
            self.screen.blit(st_txt, (bx + card_w - 95, by + 16))


        # Back button
        mx, my = pygame.mouse.get_pos()
        hovered = self._ach_back_rect.collidepoint(mx, my)
        btn_surf = pygame.Surface((130, 36), pygame.SRCALPHA)
        pygame.draw.rect(btn_surf, (20, 25, 55, 200 if hovered else 140), (0, 0, 130, 36), border_radius=12)
        pygame.draw.rect(btn_surf, Colors.CYAN if hovered else (70, 80, 130), (0, 0, 130, 36), 1, border_radius=12)
        self.screen.blit(btn_surf, self._ach_back_rect.topleft)

        back_txt = self.font_small.render("← Back", True, Colors.WHITE)
        self.screen.blit(back_txt, back_txt.get_rect(center=self._ach_back_rect.center))

    def _handle_achievements_click(self, pos):
        if hasattr(self, '_ach_back_rect') and self._ach_back_rect.collidepoint(pos):
            self.state = GameState.MENU

    # ─── Achievement Popup ───
    def _render_achievement_popup(self):
        if not self._achievement_popup:
            return
        elapsed = time.time() - self._achievement_popup_time
        # Slide in from top
        target_y = 80
        if elapsed < 0.3:
            y = int(-60 + (target_y + 60) * (elapsed / 0.3))
        elif elapsed > 2.5:
            y = int(target_y - (target_y + 60) * ((elapsed - 2.5) / 0.5))
        else:
            y = target_y

        banner_w = 400
        banner_h = 50
        bx = SCREEN_WIDTH // 2 - banner_w // 2
        banner = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
        pygame.draw.rect(banner, (30, 30, 60, 200), (0, 0, banner_w, banner_h), border_radius=10)
        pygame.draw.rect(banner, Colors.GOLD, (0, 0, banner_w, banner_h), 2, border_radius=10)
        self.screen.blit(banner, (bx, y))

        label = self.font_small.render("ACHIEVEMENT UNLOCKED", True, Colors.GOLD)
        self.screen.blit(label, label.get_rect(center=(SCREEN_WIDTH // 2, y + 15)))
        name = self.font_small.render(self._achievement_popup, True, Colors.WHITE)
        self.screen.blit(name, name.get_rect(center=(SCREEN_WIDTH // 2, y + 35)))

    # ───────────── Cleanup ─────────────
    def _cleanup(self):
        self.camera.release()
        self.hand_detector.release()
        pygame.quit()


# ═══════════════════════════════════════════════════════
#   ENTRY POINT
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    game = FruitNinjaGame()
    game.run()
