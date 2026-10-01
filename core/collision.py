"""
Collision detection — line-segment vs. circle intersection.
Determines whether the blade trail slices a fruit/bomb/powerup.
"""
import math


def point_in_circle(px, py, cx, cy, radius):
    """Check if point (px, py) is inside circle (cx, cy, radius)."""
    return (px - cx) ** 2 + (py - cy) ** 2 <= radius ** 2


def segment_intersects_circle(p1, p2, cx, cy, radius):
    """
    Check if line segment p1→p2 intersects circle (cx, cy, radius).
    Uses closest-point projection algorithm for maximum accuracy on fast swipes.
    """
    x1, y1 = float(p1[0]), float(p1[1])
    x2, y2 = float(p2[0]), float(p2[1])
    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return (x1 - cx) ** 2 + (y1 - cy) ** 2 <= radius ** 2

    # Project circle center onto segment line parameter t in [0, 1]
    t = ((cx - x1) * dx + (cy - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))

    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    dist_sq = (closest_x - cx) ** 2 + (closest_y - cy) ** 2
    return dist_sq <= radius ** 2


def blade_hits_entity(blade_segments, entity_x, entity_y, entity_radius):
    """
    Check if any segment of the blade trail intersects the entity circle.
    blade_segments: list of ((x1,y1), (x2,y2))
    Returns True on first hit.
    """
    for p1, p2 in blade_segments:
        if segment_intersects_circle(p1, p2, entity_x, entity_y, entity_radius):
            return True
    return False

