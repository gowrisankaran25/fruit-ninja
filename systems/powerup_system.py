"""
Power-up system — manages active power-ups and their durations.
"""
import time


class PowerUpSystem:
    """Tracks which power-ups are currently active and for how long."""

    def __init__(self):
        # Maps powerup_type → expiry timestamp
        self.active = {}

    def activate(self, powerup_type, duration):
        """Activate (or extend) a power-up."""
        self.active[powerup_type] = time.time() + duration

    def is_active(self, powerup_type):
        if powerup_type not in self.active:
            return False
        return time.time() < self.active[powerup_type]

    def remaining(self, powerup_type):
        if powerup_type not in self.active:
            return 0.0
        return max(0.0, self.active[powerup_type] - time.time())

    @property
    def freeze_active(self):
        return self.is_active("freeze")

    @property
    def fire_blade_active(self):
        return self.is_active("fire_blade")

    @property
    def double_score_active(self):
        return self.is_active("double_score")

    @property
    def slow_motion_active(self):
        return self.is_active("slow_motion")

    @property
    def time_scale(self):
        """Return the dt multiplier based on active slow/freeze."""
        if self.freeze_active:
            return 0.15
        if self.slow_motion_active:
            return 0.4
        return 1.0

    @property
    def score_multiplier(self):
        return 2.0 if self.double_score_active else 1.0

    def update(self):
        """Prune expired power-ups."""
        now = time.time()
        self.active = {k: v for k, v in self.active.items() if v > now}

    def get_active_list(self):
        """Return list of (type, remaining_seconds) for HUD."""
        now = time.time()
        return [
            (k, max(0, v - now))
            for k, v in self.active.items()
            if v > now
        ]

    def reset(self):
        self.active.clear()
