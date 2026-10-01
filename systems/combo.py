"""
Combo system — tracks consecutive slices and multiplier.
"""
import time
from config import COMBO_TIMEOUT, COMBO_MULTIPLIERS


class ComboSystem:
    """Manages combo counter, multiplier, and timeout."""

    def __init__(self):
        self.count = 0
        self.max_combo = 0
        self.last_slice_time = 0
        self._display_timer = 0

    @property
    def multiplier(self):
        best = 1.0
        for threshold, mult in sorted(COMBO_MULTIPLIERS.items()):
            if self.count >= threshold:
                best = mult
        return best

    @property
    def is_active(self):
        return self.count >= 2

    @property
    def display_text(self):
        if self.count >= 3:
            return f"COMBO x{self.count}"
        return ""

    def register_slice(self):
        """Call when a fruit is sliced."""
        now = time.time()
        if now - self.last_slice_time > COMBO_TIMEOUT:
            self.count = 0
        self.count += 1
        self.last_slice_time = now
        self.max_combo = max(self.max_combo, self.count)
        self._display_timer = now

    def update(self):
        """Call every frame. Resets combo if timed out."""
        now = time.time()
        if self.count > 0 and now - self.last_slice_time > COMBO_TIMEOUT:
            self.count = 0

    @property
    def show_display(self):
        """Should we show the combo HUD?"""
        if self.count >= 3:
            return True
        # Brief linger after combo breaks
        return time.time() - self._display_timer < 1.0 and self._display_timer > 0

    def reset(self):
        self.count = 0
        self.max_combo = 0
        self.last_slice_time = 0
        self._display_timer = 0
