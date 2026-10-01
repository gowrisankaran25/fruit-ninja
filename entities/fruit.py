"""
Fruit entity — physics-driven fruit that arcs across the screen.
"""
import os
import math
import random
import pygame
from config import (
    GRAVITY, FRUIT_TYPES, SCREEN_WIDTH, SCREEN_HEIGHT,
    FRUIT_MIN_VY, FRUIT_MAX_VY, FRUIT_MIN_VX, FRUIT_MAX_VX,
    FRUIT_ROTATION_SPEED_RANGE, DATA_DIR,
)

# Global caches for loaded and scaled fruit images
_FRUIT_IMAGES = {}
_FRUIT_SCALED_IMAGES = {}


def load_fruit_images():
    """Pre-load and scale fruit images for all fruit types from DATA_DIR."""
    global _FRUIT_IMAGES, _FRUIT_SCALED_IMAGES
    if _FRUIT_SCALED_IMAGES:
        return

    for f_type, info in FRUIT_TYPES.items():
        img_path = os.path.join(DATA_DIR, f"{f_type}.png")
        if os.path.exists(img_path):
            try:
                raw_img = pygame.image.load(img_path).convert_alpha()
                _FRUIT_IMAGES[f_type] = raw_img
                # Pre-scale to diameter (radius * 2) to match physics circle bounding box
                diameter = info["radius"] * 2
                scaled_img = pygame.transform.smoothscale(raw_img, (diameter, diameter))
                _FRUIT_SCALED_IMAGES[f_type] = scaled_img
            except Exception as e:
                print(f"[Fruit] Could not load image for {f_type}: {e}")


class Fruit:
    """A single fruit projectile with physics."""

    def __init__(self, fruit_type="apple", speed_mult=1.0):
        load_fruit_images()
        info = FRUIT_TYPES[fruit_type]
        self.type = fruit_type
        self.points = info["points"]
        self.color = info["color"]
        self.radius = info["radius"]
        self.juice_color = info["juice"]
        self.sliced = False
        self.missed = False
        self.slice_time = 0

        # Spawn from bottom
        self.x = random.randint(100, SCREEN_WIDTH - 100)
        self.y = SCREEN_HEIGHT + self.radius + 10
        self.vy = random.uniform(FRUIT_MIN_VY, FRUIT_MAX_VY) * speed_mult
        self.vx = random.uniform(FRUIT_MIN_VX, FRUIT_MAX_VX) * speed_mult
        self.gravity = GRAVITY
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(*FRUIT_ROTATION_SPEED_RANGE)

        # Sliced halves
        self.left_half = None
        self.right_half = None

    def update(self, dt_scale=1.0):
        """Advance physics one frame."""
        if self.sliced:
            self._update_sliced(dt_scale)
            return
        self.vy += self.gravity * dt_scale
        self.x += self.vx * dt_scale
        self.y += self.vy * dt_scale
        self.rotation += self.rotation_speed * dt_scale

        # Missed if fallen below screen
        if self.y > SCREEN_HEIGHT + self.radius + 50:
            self.missed = True

    def _update_sliced(self, dt_scale):
        """Animate the two halves falling apart."""
        if self.left_half and self.right_half:
            for h in (self.left_half, self.right_half):
                h["vy"] += self.gravity * dt_scale
                h["x"] += h["vx"] * dt_scale
                h["y"] += h["vy"] * dt_scale
                h["rotation"] += h["rot_speed"] * dt_scale

    def slice(self):
        """Mark this fruit as sliced and create two halves."""
        if self.sliced:
            return
        self.sliced = True
        self.slice_time = pygame.time.get_ticks()
        self.left_half = {
            "x": self.x - 10, "y": self.y,
            "vx": self.vx - 3, "vy": self.vy - 2,
            "rotation": self.rotation, "rot_speed": -4,
        }
        self.right_half = {
            "x": self.x + 10, "y": self.y,
            "vx": self.vx + 3, "vy": self.vy - 2,
            "rotation": self.rotation, "rot_speed": 4,
        }

    @property
    def alive(self):
        """Still on-screen and relevant?"""
        if self.missed:
            return False
        if self.sliced:
            elapsed = pygame.time.get_ticks() - self.slice_time
            return elapsed < 1500
        return True

    def draw(self, surface):
        """Render the fruit (or its sliced halves)."""
        if self.sliced:
            self._draw_sliced(surface)
        else:
            self._draw_whole(surface)

    def _draw_whole(self, surface):
        if self.type in _FRUIT_SCALED_IMAGES:
            base_img = _FRUIT_SCALED_IMAGES[self.type]
            if self.rotation != 0:
                rotated_img = pygame.transform.rotate(base_img, self.rotation)
            else:
                rotated_img = base_img

            rect = rotated_img.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(rotated_img, rect)

            # Golden sparkle effect for golden fruit
            if self.type == "golden":
                cx, cy = int(self.x), int(self.y)
                r = self.radius
                t = pygame.time.get_ticks() / 200
                for i in range(6):
                    angle = t + i * 60
                    sx = cx + int(math.cos(math.radians(angle)) * (r + 8))
                    sy = cy + int(math.sin(math.radians(angle)) * (r + 8))
                    pygame.draw.circle(surface, (255, 255, 200), (sx, sy), 3)
        else:
            # Fallback circle drawing
            cx, cy = int(self.x), int(self.y)
            r = self.radius
            pygame.draw.circle(surface, self.color, (cx, cy), r)
            highlight = tuple(min(c + 60, 255) for c in self.color)
            pygame.draw.circle(surface, highlight, (cx - r // 4, cy - r // 4), r // 3)
            pygame.draw.circle(surface, (255, 255, 255, 80), (cx, cy), r, 2)

            if self.type == "golden":
                t = pygame.time.get_ticks() / 200
                for i in range(6):
                    angle = t + i * 60
                    sx = cx + int(math.cos(math.radians(angle)) * (r + 8))
                    sy = cy + int(math.sin(math.radians(angle)) * (r + 8))
                    pygame.draw.circle(surface, (255, 255, 200), (sx, sy), 3)

    def _draw_sliced(self, surface):
        alpha = 255
        if self.slice_time:
            elapsed = pygame.time.get_ticks() - self.slice_time
            alpha = max(0, 255 - int(elapsed * 0.2))

        if self.type in _FRUIT_SCALED_IMAGES and alpha > 0:
            base_img = _FRUIT_SCALED_IMAGES[self.type]
            w, h = base_img.get_width(), base_img.get_height()
            half_w = max(1, w // 2)

            left_img = base_img.subsurface((0, 0, half_w, h))
            right_img = base_img.subsurface((half_w, 0, w - half_w, h))

            for half, half_img in zip((self.left_half, self.right_half), (left_img, right_img)):
                if half is None:
                    continue
                rot_img = pygame.transform.rotate(half_img, half["rotation"])
                if alpha < 255:
                    rot_img = rot_img.copy()
                    rot_img.set_alpha(alpha)
                rect = rot_img.get_rect(center=(int(half["x"]), int(half["y"])))
                surface.blit(rot_img, rect)
        else:
            for half in (self.left_half, self.right_half):
                if half is None:
                    continue
                cx, cy = int(half["x"]), int(half["y"])
                r = self.radius
                col = tuple(min(c, 255) for c in self.color)
                pygame.draw.circle(surface, col, (cx, cy), r)
                inner = self.juice_color
                pygame.draw.circle(surface, inner, (cx, cy), r - 6)

