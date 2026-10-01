"""
Achievement system — tracks and unlocks achievements.
"""
import json
import os
import time
from config import ACHIEVEMENTS, DATA_DIR


class AchievementSystem:
    """Checks conditions and unlocks achievements, persisted to JSON."""

    def __init__(self):
        self.unlocked = {}   # id → timestamp
        self.pending = []    # newly unlocked, to display
        self._load()

    def unlock(self, achievement_id):
        if achievement_id in self.unlocked:
            return False
        if achievement_id not in ACHIEVEMENTS:
            return False
        self.unlocked[achievement_id] = time.time()
        self.pending.append(achievement_id)
        self._save()
        return True

    def is_unlocked(self, achievement_id):
        return achievement_id in self.unlocked

    def pop_pending(self):
        """Return and clear newly unlocked achievements."""
        p = list(self.pending)
        self.pending.clear()
        return p

    def check_conditions(self, scoring, combo, level, mode_name):
        """Call each frame to auto-unlock achievements."""
        if scoring.fruits_sliced >= 1:
            self.unlock("first_slice")
        if combo.max_combo >= 20:
            self.unlock("combo_master")
        if scoring.score >= 10000:
            self.unlock("centurion")
        if level.level >= 20:
            self.unlock("ninja_master")
        if scoring.accuracy == 100 and scoring.fruits_sliced >= 20:
            self.unlock("perfectionist")

    def get_all(self):
        """Return list of (id, info_dict, unlocked_bool)."""
        result = []
        for aid, info in ACHIEVEMENTS.items():
            result.append((aid, info, aid in self.unlocked))
        return result

    # ── Persistence ──
    def _path(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        return os.path.join(DATA_DIR, "achievements.json")

    def _load(self):
        path = self._path()
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    self.unlocked = json.load(f)
            except Exception:
                self.unlocked = {}

    def _save(self):
        path = self._path()
        with open(path, "w") as f:
            json.dump(self.unlocked, f, indent=2)
