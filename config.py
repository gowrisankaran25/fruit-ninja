"""
Fruit Ninja AI — Configuration
All game constants, colors, and tuning parameters.
"""
import os

# ──────────────────── Paths ────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DATA_DIR = os.path.join(BASE_DIR, "data")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")

# ──────────────────── Display ────────────────────
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Fruit Ninja"

# ──────────────────── Colors (RGB) ────────────────────
class Colors:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (220, 50, 50)
    GREEN = (50, 200, 80)
    BLUE = (50, 120, 220)
    YELLOW = (255, 210, 50)
    ORANGE = (255, 150, 30)
    PURPLE = (160, 80, 220)
    PINK = (255, 100, 150)
    CYAN = (0, 220, 240)
    GOLD = (255, 200, 50)
    DARK_BG = (15, 15, 30)
    DARK_PANEL = (25, 25, 50)
    MENU_GRADIENT_TOP = (10, 10, 40)
    MENU_GRADIENT_BOT = (30, 10, 60)
    HUD_BG = (0, 0, 0, 150)
    BLADE_COLOR = (200, 230, 255)
    BLADE_GLOW = (100, 180, 255)
    BOMB_RED = (200, 30, 30)
    COMBO_FIRE = (255, 120, 20)

# ──────────────────── Fruits ────────────────────
FRUIT_TYPES = {
    "apple":      {"points": 10, "color": (220, 40, 40),   "radius": 35, "juice": (220, 40, 40)},
    "banana":     {"points": 15, "color": (255, 220, 50),  "radius": 32, "juice": (255, 230, 100)},
    "orange":     {"points": 20, "color": (255, 150, 30),  "radius": 34, "juice": (255, 180, 50)},
    "watermelon": {"points": 25, "color": (40, 180, 60),   "radius": 42, "juice": (220, 50, 50)},
    "pineapple":  {"points": 30, "color": (200, 180, 40),  "radius": 38, "juice": (255, 230, 80)},
    "golden":     {"points": 50, "color": (255, 200, 50),  "radius": 30, "juice": (255, 220, 100)},
}

# ──────────────────── Bombs ────────────────────
BOMB_TYPES = {
    "normal":  {"lives_lost": 1, "radius": 35, "color": (60, 60, 60)},
    "mega":    {"lives_lost": 2, "radius": 45, "color": (80, 20, 20)},
}

# ──────────────────── Physics ────────────────────
GRAVITY = 0.35
FRUIT_MIN_VY = -14
FRUIT_MAX_VY = -10
FRUIT_MIN_VX = -4
FRUIT_MAX_VX = 4
FRUIT_ROTATION_SPEED_RANGE = (-5, 5)

# ──────────────────── Gameplay ────────────────────
MAX_LIVES = 3
COMBO_TIMEOUT = 1.5          # seconds to keep combo alive
COMBO_MULTIPLIERS = {
    1: 1.0, 2: 1.0, 3: 1.5,
    5: 2.0, 10: 3.0, 20: 5.0,
}
BLADE_TRAIL_LENGTH = 20
BLADE_MIN_SPEED = 5          # pixels/frame to count as slice

# ──────────────────── Difficulty ────────────────────
DIFFICULTY_LEVELS = {
    1:  {"spawn_rate": 1.8, "max_fruits": 3, "bomb_chance": 0.00, "speed_mult": 1.0, "label": "Beginner"},
    3:  {"spawn_rate": 1.5, "max_fruits": 4, "bomb_chance": 0.05, "speed_mult": 1.1, "label": "Easy"},
    5:  {"spawn_rate": 1.2, "max_fruits": 5, "bomb_chance": 0.10, "speed_mult": 1.2, "label": "Medium"},
    8:  {"spawn_rate": 1.0, "max_fruits": 6, "bomb_chance": 0.15, "speed_mult": 1.35, "label": "Hard"},
    10: {"spawn_rate": 0.8, "max_fruits": 7, "bomb_chance": 0.20, "speed_mult": 1.5, "label": "Expert"},
    15: {"spawn_rate": 0.6, "max_fruits": 8, "bomb_chance": 0.25, "speed_mult": 1.7, "label": "Master"},
    20: {"spawn_rate": 0.45,"max_fruits": 10,"bomb_chance": 0.30, "speed_mult": 2.0, "label": "Ninja"},
}

# ──────────────────── Power‑ups ────────────────────
POWERUP_TYPES = {
    "freeze":       {"duration": 5.0, "color": (100, 200, 255), "symbol": "❄️", "label": "FREEZE"},
    "fire_blade":   {"duration": 5.0, "color": (255, 100, 30),  "symbol": "🔥", "label": "FIRE BLADE"},
    "double_score": {"duration": 8.0, "color": (255, 215, 0),   "symbol": "💎", "label": "DOUBLE SCORE"},
    "slow_motion":  {"duration": 5.0, "color": (180, 100, 255), "symbol": "🌀", "label": "SLOW MO"},
}
POWERUP_SPAWN_INTERVAL = 25  # seconds between powerup spawns

# ──────────────────── Boss ────────────────────
BOSS_HP = 20
BOSS_RADIUS = 80
BOSS_SCORE = 1000

# ──────────────────── Achievements ────────────────────
ACHIEVEMENTS = {
    "first_slice":   {"name": "🥇 First Slice",    "desc": "Slice your first fruit"},
    "combo_master":  {"name": "🔥 Combo Master",   "desc": "Get a 20× combo"},
    "bomb_dodger":   {"name": "💣 Bomb Dodger",    "desc": "Complete level without hitting a bomb"},
    "speed_demon":   {"name": "⚡ Speed Demon",    "desc": "Slice 10 fruits in 5 seconds"},
    "ninja_master":  {"name": "👑 Ninja Master",   "desc": "Reach Level 20"},
    "centurion":     {"name": "💯 Centurion",      "desc": "Score 10,000 points in one game"},
    "boss_slayer":   {"name": "🗡️ Boss Slayer",    "desc": "Defeat the Mega Watermelon"},
    "zen_master":    {"name": "🧘 Zen Master",     "desc": "Slice 200 fruits in Zen Mode"},
    "perfectionist": {"name": "✨ Perfectionist",  "desc": "100% accuracy in a full game"},
}

# ──────────────────── Game Modes ────────────────────
GAME_MODES = {
    "classic":   {"lives": 3, "timer": None, "bombs": True,  "label": "Classic"},
    "arcade":    {"lives": 99,"timer": 60,   "bombs": True,  "label": "Arcade"},
    "zen":       {"lives": 99,"timer": 90,   "bombs": False, "label": "Zen"},
    "survival":  {"lives": 1, "timer": None, "bombs": True,  "label": "Survival"},
}

# ──────────────────── Camera ────────────────────
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_INDEX = 0
HAND_CONFIDENCE = 0.65
HAND_TRACKING_CONFIDENCE = 0.65
SMOOTHING_WINDOW = 5
ACTIVE_MARGIN = 0.05         # 5% margin for effortless full-screen reach

