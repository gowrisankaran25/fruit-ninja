"""
Gesture Recognizer — detects semantic gestures from hand landmarks.
Gestures: SWIPE, OPEN_PALM, FIST, PINCH, THUMBS_UP, NONE
"""
import math
import numpy as np
from vision.hand_detector import HandDetector


class Gesture:
    NONE = "none"
    SWIPE = "swipe"
    OPEN_PALM = "open_palm"
    FIST = "fist"
    PINCH = "pinch"
    THUMBS_UP = "thumbs_up"


class GestureRecognizer:
    """Recognises high-level gestures from MediaPipe landmarks."""

    def __init__(self):
        self._prev_index_pos = None
        self._swipe_history = []    # last N index positions

    def _finger_is_extended(self, lm, tip_idx, pip_idx):
        """A finger is extended if distance from wrist (lm[0]) to tip is greater than to pip."""
        d_tip = math.hypot(lm[tip_idx][0] - lm[0][0], lm[tip_idx][1] - lm[0][1])
        d_pip = math.hypot(lm[pip_idx][0] - lm[0][0], lm[pip_idx][1] - lm[0][1])
        return d_tip > d_pip * 1.15

    def _thumb_is_extended(self, lm):
        """Thumb: compare x distance from wrist; extended if tip farther."""
        return abs(lm[4][0] - lm[0][0]) > abs(lm[3][0] - lm[0][0])

    def recognize(self, landmarks):
        """
        Given a 21×3 normalised landmark array, return a Gesture string
        plus a dict of metadata (e.g. swipe_direction, swipe_speed).
        """
        lm = landmarks
        meta = {}

        # Count extended fingers
        fingers = []
        fingers.append(self._thumb_is_extended(lm))
        fingers.append(self._finger_is_extended(lm, 8, 6))   # index
        fingers.append(self._finger_is_extended(lm, 12, 10)) # middle
        fingers.append(self._finger_is_extended(lm, 16, 14)) # ring
        fingers.append(self._finger_is_extended(lm, 20, 18)) # pinky
        count = sum(fingers)
        meta["fingers_extended"] = count
        meta["finger_states"] = fingers

        # Pinch: thumb tip very close to index tip
        pinch_dist = math.dist(lm[4][:2], lm[8][:2])
        if pinch_dist < 0.05:
            return Gesture.PINCH, meta

        # Fist: no fingers extended
        if count == 0:
            return Gesture.FIST, meta

        # Thumbs up: only thumb extended
        if fingers[0] and count == 1:
            return Gesture.THUMBS_UP, meta

        # Open palm: all five extended
        if count == 5:
            return Gesture.OPEN_PALM, meta

        return Gesture.NONE, meta

    def detect_swipe(self, current_pos, prev_pos, dt):
        """
        Given current & previous screen-space index-tip positions,
        return (is_swipe, direction_vector, speed).
        """
        if prev_pos is None or dt <= 0:
            return False, (0, 0), 0.0
        dx = current_pos[0] - prev_pos[0]
        dy = current_pos[1] - prev_pos[1]
        dist = math.hypot(dx, dy)
        speed = dist / dt  # pixels per second
        direction = (dx, dy)
        is_swipe = speed > 300  # threshold
        return is_swipe, direction, speed
