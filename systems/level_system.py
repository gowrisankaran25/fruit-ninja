"""
Level system — progressive difficulty scaling.
"""
from config import DIFFICULTY_LEVELS


class LevelSystem:
    """Manages level progression based on score thresholds."""

    SCORE_PER_LEVEL = 500  # points needed per level-up

    def __init__(self):
        self.level = 1
        self._last_level = 1
        self.leveled_up = False  # flag for one frame
        self._current_score = 0

    def update(self, current_score):
        """Recalculate level from score."""
        self._last_level = self.level
        self._current_score = current_score
        self.level = max(1, current_score // self.SCORE_PER_LEVEL + 1)
        self.leveled_up = self.level > self._last_level

    @property
    def progress(self):
        """Return 0.0 -> 1.0 progress to next level."""
        score_in_level = self._current_score % self.SCORE_PER_LEVEL
        return score_in_level / self.SCORE_PER_LEVEL

    def get_difficulty(self):
        """Return the difficulty dict for the current level."""
        best = None
        for threshold in sorted(DIFFICULTY_LEVELS.keys()):
            if self.level >= threshold:
                best = DIFFICULTY_LEVELS[threshold]
        return best or DIFFICULTY_LEVELS[1]

    @property
    def label(self):
        return self.get_difficulty().get("label", "Unknown")

    @property
    def is_boss_level(self):
        """Boss appears every 10 levels."""
        return self.level > 1 and self.level % 10 == 0

    def reset(self):
        self.level = 1
        self._last_level = 1
        self.leveled_up = False
        self._current_score = 0

