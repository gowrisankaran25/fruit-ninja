"""
Power-up entity — grants temporary abilities.
"""
import random
import math
import pygame
from config import POWERUP_TYPES, SCREEN_WIDTH, SCREEN_HEIGHT, GRAVITY, FRUIT_MIN_VY, FRUIT_MAX_VY


class PowerUp:
    """A collectible power-up that arcs across the screen like a fruit."""

    def __init__(self, powerup_type="freeze", speed_mult=1.0):
        info = POWERUP_TYPES[powerup_type]
        self.type = powerup_type
        self.duration = info["duration"]
        self.color = info["color"]
        self.symbol = info["symbol"]
        self.label = info["label"]
        self.radius = 28
        self.collected = False
        self.collect_time = 0

        self.x = random.randint(150, SCREEN_WIDTH - 150)
        self.y = SCREEN_HEIGHT + self.radius + 10
        self.vy = random.uniform(FRUIT_MIN_VY, FRUIT_MAX_VY) * speed_mult * 0.9
        self.vx = random.uniform(-2, 2)
        self.gravity = GRAVITY
        self.rotation = 0

    def update(self, dt_scale=1.0):
        self.vy += self.gravity * dt_scale
        self.x += self.vx * dt_scale
        self.y += self.vy * dt_scale
        self.rotation += 2 * dt_scale

    def collect(self):
        self.collected = True
        self.collect_time = pygame.time.get_ticks()

    @property
    def alive(self):
        if self.collected:
            return pygame.time.get_ticks() - self.collect_time < 600
        return self.y < SCREEN_HEIGHT + self.radius + 50

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        t = pygame.time.get_ticks() / 500.0

        if self.collected:
            elapsed = pygame.time.get_ticks() - self.collect_time
            alpha = max(0, 255 - int(elapsed * 0.5))
            expand = r + int(elapsed * 0.1)
            pygame.draw.circle(surface, self.color, (cx, cy), expand, 3)
            return

        # Pulsating glow
        glow_r = r + int(4 * math.sin(t * 3))
        glow_surface = pygame.Surface((glow_r * 4, glow_r * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*self.color, 40), (glow_r * 2, glow_r * 2), glow_r * 2)
        surface.blit(glow_surface, (cx - glow_r * 2, cy - glow_r * 2))

        # Main circle
        pygame.draw.circle(surface, self.color, (cx, cy), r)
        highlight = tuple(min(c + 80, 255) for c in self.color)
        pygame.draw.circle(surface, highlight, (cx, cy), r - 6)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), r, 2)

        # Orbiting sparkles
        for i in range(4):
            angle = t * 200 + i * 90
            sx = cx + int(math.cos(math.radians(angle)) * (r + 6))
            sy = cy + int(math.sin(math.radians(angle)) * (r + 6))
            pygame.draw.circle(surface, (255, 255, 255), (sx, sy), 2)
