"""
Screen effects — shake, flash, slow-mo overlay.
"""
import random
import pygame


class ScreenEffects:
    """Manages screen shake and damage flash."""

    def __init__(self):
        self.shake_intensity = 0
        self.shake_decay = 0.85
        self.flash_alpha = 0
        self.flash_color = (255, 0, 0)

    def trigger_shake(self, intensity=12):
        self.shake_intensity = intensity

    def trigger_flash(self, color=(255, 0, 0), alpha=100):
        self.flash_color = color
        self.flash_alpha = alpha

    def update(self):
        self.shake_intensity *= self.shake_decay
        if self.shake_intensity < 0.5:
            self.shake_intensity = 0
        self.flash_alpha = max(0, self.flash_alpha - 6)

    def get_offset(self):
        if self.shake_intensity < 1:
            return (0, 0)
        ox = random.randint(-int(self.shake_intensity), int(self.shake_intensity))
        oy = random.randint(-int(self.shake_intensity), int(self.shake_intensity))
        return (ox, oy)

    def draw_flash(self, surface):
        if self.flash_alpha > 0:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((*self.flash_color, int(self.flash_alpha)))
            surface.blit(overlay, (0, 0))
