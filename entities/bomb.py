"""
Bomb entity — penalises the player on contact.
"""
import random
import pygame
import math
from config import BOMB_TYPES, SCREEN_WIDTH, SCREEN_HEIGHT, GRAVITY, FRUIT_MIN_VY, FRUIT_MAX_VY


class Bomb:
    """A bomb that costs lives when sliced."""

    def __init__(self, bomb_type="normal", speed_mult=1.0):
        info = BOMB_TYPES[bomb_type]
        self.type = bomb_type
        self.lives_cost = info["lives_lost"]
        self.radius = info["radius"]
        self.color = info["color"]
        self.hit = False
        self.hit_time = 0

        self.x = random.randint(120, SCREEN_WIDTH - 120)
        self.y = SCREEN_HEIGHT + self.radius + 10
        self.vy = random.uniform(FRUIT_MIN_VY, FRUIT_MAX_VY) * speed_mult
        self.vx = random.uniform(-3, 3) * speed_mult
        self.gravity = GRAVITY
        self.rotation = 0
        self.rotation_speed = random.uniform(-3, 3)

    def update(self, dt_scale=1.0):
        self.vy += self.gravity * dt_scale
        self.x += self.vx * dt_scale
        self.y += self.vy * dt_scale
        self.rotation += self.rotation_speed * dt_scale

    def trigger(self):
        if not self.hit:
            self.hit = True
            self.hit_time = pygame.time.get_ticks()

    @property
    def alive(self):
        if self.hit:
            return pygame.time.get_ticks() - self.hit_time < 800
        return self.y < SCREEN_HEIGHT + self.radius + 50

    @property
    def off_screen(self):
        return self.y > SCREEN_HEIGHT + self.radius + 50

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        r = self.radius

        if self.hit:
            # Explosion effect
            elapsed = pygame.time.get_ticks() - self.hit_time
            expand = r + int(elapsed * 0.15)
            alpha = max(0, 255 - int(elapsed * 0.4))
            pygame.draw.circle(surface, (255, 80, 20), (cx, cy), expand)
            pygame.draw.circle(surface, (255, 200, 50), (cx, cy), expand // 2)
            return

        # Bomb body
        pygame.draw.circle(surface, self.color, (cx, cy), r)
        pygame.draw.circle(surface, (40, 40, 40), (cx, cy), r - 4)
        # Highlight
        pygame.draw.circle(surface, (90, 90, 90), (cx - r // 4, cy - r // 4), r // 4)
        # Fuse
        fuse_end_x = cx + int(math.cos(math.radians(self.rotation + 45)) * (r + 8))
        fuse_end_y = cy + int(math.sin(math.radians(self.rotation + 45)) * (r + 8))
        pygame.draw.line(surface, (180, 140, 60), (cx, cy - r + 4), (fuse_end_x, fuse_end_y - r), 3)
        # Spark on fuse
        t = pygame.time.get_ticks()
        if t % 300 < 150:
            pygame.draw.circle(surface, (255, 200, 50), (fuse_end_x, fuse_end_y - r), 4)

        # Skull/cross on mega
        if self.type == "mega":
            pygame.draw.line(surface, (200, 30, 30), (cx - 8, cy - 8), (cx + 8, cy + 8), 3)
            pygame.draw.line(surface, (200, 30, 30), (cx + 8, cy - 8), (cx - 8, cy + 8), 3)
