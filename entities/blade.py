"""
Blade — visual trail of the player's hand movement.
Includes Chaikin corner-cutting curve smoothing for smooth visual trails.
"""
import pygame
import math
from config import Colors


def _smooth_trail(points, iterations=2):
    """
    Apply Chaikin's corner cutting algorithm to smooth raw jagged trail points
    into a smooth, continuous curve.
    """
    if len(points) < 3:
        return points

    curr = list(points)
    for _ in range(iterations):
        smoothed = [curr[0]]
        for i in range(len(curr) - 1):
            p0 = curr[i]
            p1 = curr[i + 1]
            q = (0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1])
            r = (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])
            smoothed.append(q)
            smoothed.append(r)
        smoothed.append(curr[-1])
        curr = smoothed
    return curr


class Blade:
    """Renders the slicing blade trail from a list of screen positions."""

    def __init__(self):
        self.active = False
        self.fire_mode = False

    def draw(self, surface, trail_points, is_slicing=False):
        """
        Draw the blade trail on *surface*.
        trail_points: list of (x, y) screen positions, newest last.
        """
        if len(trail_points) < 2:
            return

        self.active = is_slicing

        # Smooth raw trail coordinates to eliminate jagged edges
        pts = _smooth_trail(trail_points, iterations=2)
        n = len(pts)

        if n < 2:
            return

        # Draw multi-pass glowing blade curve
        for i in range(1, n):
            t = i / n  # 0->1 (1 is newest tip)
            thickness = max(2, int(t * 10))

            if self.fire_mode:
                r = 255
                g = int(100 + 155 * t)
                b = int(40 * (1 - t))
                glow_col = (255, 120, 20)
            else:
                r = int(160 + 95 * t)
                g = int(220 + 35 * t)
                b = 255
                glow_col = Colors.BLADE_GLOW

            p1 = (int(pts[i - 1][0]), int(pts[i - 1][1]))
            p2 = (int(pts[i][0]), int(pts[i][1]))

            # Outer glow line
            pygame.draw.line(surface, (*glow_col, 80), p1, p2, thickness + 4)
            # Bright core line
            pygame.draw.line(surface, (r, g, b), p1, p2, thickness)

        # Tip flare highlight when slicing
        if is_slicing:
            tip = (int(pts[-1][0]), int(pts[-1][1]))
            flare_col = (255, 180, 50) if self.fire_mode else (220, 240, 255)
            flare_surf = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(flare_surf, (*flare_col, 90), (18, 18), 18)
            pygame.draw.circle(flare_surf, (255, 255, 255, 220), (18, 18), 8)
            surface.blit(flare_surf, (tip[0] - 18, tip[1] - 18))

