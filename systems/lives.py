"""
Lives system — manages player health.
"""
from config import MAX_LIVES


class LivesSystem:
    """Tracks remaining lives with visual state helpers."""

    def __init__(self, max_lives=MAX_LIVES):
        self.max_lives = max_lives
        self.lives = max_lives
        self.damage_flash = 0  # frames of damage flash remaining

    @property
    def is_alive(self):
        return self.lives > 0

    def lose(self, amount=1):
        self.lives = max(0, self.lives - amount)
        self.damage_flash = 15  # frames

    def gain(self, amount=1):
        self.lives = min(self.max_lives, self.lives + amount)

    def update(self):
        if self.damage_flash > 0:
            self.damage_flash -= 1

    def reset(self, max_lives=None):
        if max_lives is not None:
            self.max_lives = max_lives
        self.lives = self.max_lives
        self.damage_flash = 0
