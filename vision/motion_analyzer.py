"""
Motion Analyzer — tracks hand movement over time.
Computes velocity, acceleration, swipe trajectories, and smoothing.
"""
import math
import time
import numpy as np
from collections import deque
from config import BLADE_TRAIL_LENGTH, BLADE_MIN_SPEED, SCREEN_WIDTH, SCREEN_HEIGHT


class MotionAnalyzer:
    """
    Maintains a rolling window of index-fingertip positions
    and derives velocity, acceleration, and swipe state.
    """

    def __init__(self, trail_length=BLADE_TRAIL_LENGTH):
        self.trail = deque(maxlen=trail_length)
        self._prev_pos = None
        self._prev_time = None
        self.velocity = (0.0, 0.0)
        self.speed = 0.0
        self.acceleration = 0.0
        self._prev_speed = 0.0
        self.is_slicing = False

    def update(self, screen_pos):
        """
        Feed a new (x, y) screen-space position of the index fingertip.
        Call once per frame.
        """
        now = time.time()
        if screen_pos is None:
            self._prev_pos = None
            self._prev_time = None
            self.is_slicing = False
            return

        self.trail.append(screen_pos)

        if self._prev_pos is not None and self._prev_time is not None:
            dt = now - self._prev_time
            if dt > 0:
                dx = screen_pos[0] - self._prev_pos[0]
                dy = screen_pos[1] - self._prev_pos[1]
                self.velocity = (dx / dt, dy / dt)
                self.speed = math.hypot(dx, dy) / dt
                self.acceleration = (self.speed - self._prev_speed) / dt
                self._prev_speed = self.speed
        else:
            self.velocity = (0, 0)
            self.speed = 0
            self.acceleration = 0
            self._prev_speed = 0

        # Is slicing = fast enough movement between consecutive frames
        frame_dist = 0
        if self._prev_pos is not None:
            frame_dist = math.hypot(
                screen_pos[0] - self._prev_pos[0],
                screen_pos[1] - self._prev_pos[1],
            )
        self.is_slicing = frame_dist > BLADE_MIN_SPEED

        self._prev_pos = screen_pos
        self._prev_time = now

    def get_trail_points(self):
        """Return the list of recent positions (for blade rendering)."""
        return list(self.trail)

    def get_blade_segments(self):
        """
        Return list of ((x1,y1),(x2,y2)) line segments
        representing the blade trail.
        """
        pts = list(self.trail)
        if len(pts) < 2:
            return []
        return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]

    def clear(self):
        self.trail.clear()
        self._prev_pos = None
        self._prev_time = None
        self.velocity = (0, 0)
        self.speed = 0
        self.acceleration = 0
        self.is_slicing = False
