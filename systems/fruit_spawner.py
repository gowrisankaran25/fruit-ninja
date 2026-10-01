"""
Fruit Spawner — controls when and what fruits/bombs/powerups appear.
"""
import random
import time
from entities.fruit import Fruit
from entities.bomb import Bomb
from entities.powerup import PowerUp
from config import FRUIT_TYPES, POWERUP_TYPES, POWERUP_SPAWN_INTERVAL


class FruitSpawner:
    """Manages timed spawning of fruits, bombs, and power-ups."""

    def __init__(self):
        self.last_spawn = time.time()
        self.last_powerup = time.time()
        self.spawn_rate = 1.8     # seconds between waves
        self.max_fruits = 3
        self.bomb_chance = 0.0
        self.speed_mult = 1.0

    def configure(self, spawn_rate, max_fruits, bomb_chance, speed_mult):
        self.spawn_rate = spawn_rate
        self.max_fruits = max_fruits
        self.bomb_chance = bomb_chance
        self.speed_mult = speed_mult

    def update(self, current_fruits_count):
        """
        Return lists: (new_fruits, new_bombs, new_powerups)
        Called once per frame.
        """
        now = time.time()
        new_fruits = []
        new_bombs = []
        new_powerups = []

        if now - self.last_spawn >= self.spawn_rate:
            self.last_spawn = now
            # Spawn a wave
            wave_size = random.randint(1, min(self.max_fruits, 4))
            for _ in range(wave_size):
                if current_fruits_count + len(new_fruits) + len(new_bombs) >= self.max_fruits:
                    break
                if random.random() < self.bomb_chance:
                    btype = "mega" if random.random() < 0.15 else "normal"
                    new_bombs.append(Bomb(btype, self.speed_mult))
                else:
                    ftype = self._pick_fruit_type()
                    new_fruits.append(Fruit(ftype, self.speed_mult))

        # Power-up spawn
        if now - self.last_powerup >= POWERUP_SPAWN_INTERVAL:
            self.last_powerup = now
            ptype = random.choice(list(POWERUP_TYPES.keys()))
            new_powerups.append(PowerUp(ptype, self.speed_mult))

        return new_fruits, new_bombs, new_powerups

    def _pick_fruit_type(self):
        """Weighted random fruit selection (rarer fruits less common)."""
        weights = {
            "apple": 30, "banana": 25, "orange": 20,
            "watermelon": 15, "pineapple": 8, "golden": 2,
        }
        types = list(weights.keys())
        w = [weights[t] for t in types]
        return random.choices(types, weights=w, k=1)[0]
