"""
Particle system — juice splashes, explosion fragments, score popups.
"""
import random
import math
import pygame


class Particle:
    """A single animated particle."""

    def __init__(self, x, y, color, vx=None, vy=None,
                 radius=4, lifetime=800, gravity=0.15, shrink=True):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx if vx is not None else random.uniform(-5, 5)
        self.vy = vy if vy is not None else random.uniform(-8, -2)
        self.radius = radius
        self.max_radius = radius
        self.lifetime = lifetime
        self.birth = pygame.time.get_ticks()
        self.gravity = gravity
        self.shrink = shrink

    @property
    def alive(self):
        return pygame.time.get_ticks() - self.birth < self.lifetime

    @property
    def age_ratio(self):
        return min(1.0, (pygame.time.get_ticks() - self.birth) / self.lifetime)

    def update(self):
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        if self.shrink:
            self.radius = max(0, int(self.max_radius * (1 - self.age_ratio)))

    def draw(self, surface):
        if self.radius <= 0:
            return
        alpha = int(255 * (1 - self.age_ratio))
        r = self.radius
        s = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        col = (*self.color[:3], alpha)
        pygame.draw.circle(s, col, (r * 2, r * 2), r)
        surface.blit(s, (int(self.x) - r * 2, int(self.y) - r * 2))


class ScorePopup:
    """Floating score text that drifts upward and fades."""

    def __init__(self, x, y, text, color=(255, 255, 255), size=28):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.size = size
        self.birth = pygame.time.get_ticks()
        self.lifetime = 1200
        self.vy = -2.5

    @property
    def alive(self):
        return pygame.time.get_ticks() - self.birth < self.lifetime

    @property
    def age_ratio(self):
        return min(1.0, (pygame.time.get_ticks() - self.birth) / self.lifetime)

    def update(self):
        self.y += self.vy
        self.vy *= 0.98

    def draw(self, surface, font):
        alpha = int(255 * (1 - self.age_ratio))
        scale = 1.0 + 0.3 * (1 - self.age_ratio)
        render_size = max(10, int(self.size * scale))
        try:
            f = pygame.font.Font(None, render_size)
        except Exception:
            f = font
        txt = f.render(self.text, True, self.color)
        txt.set_alpha(alpha)
        rect = txt.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(txt, rect)


class ParticleSystem:
    """Manages collections of particles and score popups."""

    def __init__(self):
        self.particles = []
        self.popups = []

    def emit_juice(self, x, y, color, count=15):
        """Spawn juice splash particles at (x, y)."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 3
            r = random.randint(2, 6)
            lt = random.randint(400, 900)
            self.particles.append(
                Particle(x, y, color, vx, vy, r, lt)
            )

    def emit_explosion(self, x, y, count=25):
        """Spawn explosion particles (orange/red)."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 10)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice([
                (255, 80, 20), (255, 200, 50), (255, 120, 30), (200, 50, 10)
            ])
            r = random.randint(3, 7)
            self.particles.append(
                Particle(x, y, color, vx, vy, r, 600)
            )

    def emit_sparkle(self, x, y, color=(255, 255, 200), count=8):
        """Small sparkle burst."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 4)
            self.particles.append(
                Particle(x, y, color,
                         math.cos(angle) * speed,
                         math.sin(angle) * speed,
                         random.randint(1, 3), 500)
            )

    def add_popup(self, x, y, text, color=(255, 255, 255), size=28):
        self.popups.append(ScorePopup(x, y, text, color, size))

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]
        for p in self.popups:
            p.update()
        self.popups = [p for p in self.popups if p.alive]

    def draw(self, surface, font=None):
        for p in self.particles:
            p.draw(surface)
        if font:
            for p in self.popups:
                p.draw(surface, font)

    def clear(self):
        self.particles.clear()
        self.popups.clear()
