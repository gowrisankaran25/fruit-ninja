"""
Scoring system — manages score, high scores, and accuracy.
"""
import json
import os
from config import DATA_DIR


class ScoringSystem:
    """Tracks score, fruits sliced, accuracy, and persists high scores."""

    def __init__(self):
        self.score = 0
        self.high_score = 0
        self.fruits_sliced = 0
        self.fruits_missed = 0
        self.bombs_hit = 0
        self.total_slices = 0  # blade activations
        self._load_high_score()

    def add_score(self, points, multiplier=1.0):
        gain = int(points * multiplier)
        self.score += gain
        return gain

    def fruit_sliced(self):
        self.fruits_sliced += 1

    def fruit_missed(self):
        self.fruits_missed += 1

    def bomb_hit(self):
        self.bombs_hit += 1

    @property
    def accuracy(self):
        total = self.fruits_sliced + self.fruits_missed
        if total == 0:
            return 0.0
        return self.fruits_sliced / total * 100

    @property
    def is_new_high(self):
        return self.score > self.high_score

    def finalize(self):
        """Call at game end to persist high score."""
        if self.score > self.high_score:
            self.high_score = self.score
            self._save_high_score()

    def reset(self):
        self.score = 0
        self.fruits_sliced = 0
        self.fruits_missed = 0
        self.bombs_hit = 0
        self.total_slices = 0

    # ── Persistence ──
    def _scores_path(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        return os.path.join(DATA_DIR, "scores.json")

    def _load_high_score(self):
        path = self._scores_path()
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                self.high_score = data.get("high_score", 0)
            except Exception:
                self.high_score = 0
        else:
            self.high_score = 0

    def _save_high_score(self):
        path = self._scores_path()
        with open(path, "w") as f:
            json.dump({"high_score": self.high_score}, f, indent=2)
