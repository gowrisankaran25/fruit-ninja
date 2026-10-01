"""
Hand Detector — MediaPipe 21-landmark hand detection.
Supports both MediaPipe Tasks API (MediaPipe 1.0+) and legacy mp.solutions API.
Returns normalised and screen-space landmark positions.
"""
import os
import urllib.request
import cv2
import mediapipe as mp
import numpy as np
from collections import deque
from config import HAND_CONFIDENCE, HAND_TRACKING_CONFIDENCE, SMOOTHING_WINDOW


class HandDetector:
    """Wraps MediaPipe Hands for 21-landmark detection with position smoothing."""

    # Landmark indices
    WRIST = 0
    THUMB_TIP = 4
    INDEX_TIP = 8
    MIDDLE_TIP = 12
    RING_TIP = 16
    PINKY_TIP = 20
    INDEX_MCP = 5
    MIDDLE_MCP = 9

    def __init__(self, max_hands=1,
                 min_detection=HAND_CONFIDENCE,
                 min_tracking=HAND_TRACKING_CONFIDENCE):
        self.use_tasks = False
        self.pos_history = deque(maxlen=SMOOTHING_WINDOW)

        if hasattr(mp, 'tasks') and hasattr(mp.tasks, 'vision'):
            try:
                model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'hand_landmarker.task'))
                if not os.path.exists(model_path):
                    url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
                    urllib.request.urlretrieve(url, model_path)

                from mediapipe.tasks import python
                from mediapipe.tasks.python import vision
                base_options = python.BaseOptions(model_asset_path=model_path)
                options = vision.HandLandmarkerOptions(
                    base_options=base_options,
                    num_hands=max_hands,
                    min_hand_detection_confidence=min_detection,
                    min_hand_presence_confidence=min_tracking,
                    min_tracking_confidence=min_tracking
                )
                self.detector = vision.HandLandmarker.create_from_options(options)
                self.use_tasks = True
            except Exception as e:
                print(f"[HandDetector] Tasks API initialization failed: {e}")

        if not self.use_tasks and hasattr(mp, 'solutions') and hasattr(mp.solutions, 'hands'):
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=max_hands,
                min_detection_confidence=min_detection,
                min_tracking_confidence=min_tracking,
            )
            self.mp_draw = mp.solutions.drawing_utils

    def detect(self, frame_rgb):
        """
        Process an RGB frame and return a list of hand results.
        Each result is a dict with 'landmarks' (21×3 numpy array, normalised 0-1)
        and 'handedness'.
        """
        if self.use_tasks:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            results = self.detector.detect(mp_image)
            hands = []
            if results.hand_landmarks:
                for hand_lms, handedness in zip(results.hand_landmarks, results.handedness):
                    lm = np.array([(p.x, p.y, p.z) for p in hand_lms], dtype=np.float32)
                    label = handedness[0].category_name if handedness else "Right"
                    hands.append({
                        "landmarks": lm,
                        "raw": hand_lms,
                        "handedness": label
                    })
            return hands
        elif hasattr(self, 'hands'):
            results = self.hands.process(frame_rgb)
            hands = []
            if results.multi_hand_landmarks:
                for hand_lm, hand_info in zip(
                    results.multi_hand_landmarks,
                    results.multi_handedness,
                ):
                    lm = np.array(
                        [(p.x, p.y, p.z) for p in hand_lm.landmark],
                        dtype=np.float32,
                    )
                    hands.append({
                        "landmarks": lm,
                        "raw": hand_lm,
                        "handedness": hand_info.classification[0].label,
                    })
            return hands
        return []

    def to_screen(self, landmarks, screen_w, screen_h):
        """Convert normalised landmarks → pixel coordinates (Nx2)."""
        pts = landmarks[:, :2].copy()
        pts[:, 0] *= screen_w
        pts[:, 1] *= screen_h
        return pts.astype(int)

    def smooth_position(self, pos):
        """
        Apply a simple moving average smoothing over recent (x, y) coordinates
        to reduce cursor jitter during gameplay.
        """
        if pos is None:
            self.pos_history.clear()
            return None
        self.pos_history.append(pos)
        avg_x = sum(p[0] for p in self.pos_history) / len(self.pos_history)
        avg_y = sum(p[1] for p in self.pos_history) / len(self.pos_history)
        return (int(avg_x), int(avg_y))

    def draw_landmarks(self, frame, raw_landmarks):
        """Draw MediaPipe-style landmarks on a BGR frame (for debug overlay)."""
        if hasattr(self, 'mp_draw'):
            self.mp_draw.draw_landmarks(
                frame, raw_landmarks, self.mp_hands.HAND_CONNECTIONS,
            )
        else:
            h, w, _ = frame.shape
            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),
                (0, 5), (5, 6), (6, 7), (7, 8),
                (5, 9), (9, 10), (10, 11), (11, 12),
                (9, 13), (13, 14), (14, 15), (15, 16),
                (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)
            ]
            if isinstance(raw_landmarks, np.ndarray):
                pts = [(int(p[0] * w), int(p[1] * h)) for p in raw_landmarks]
            else:
                pts = [(int(p.x * w), int(p.y * h)) for p in raw_landmarks]

            for s, e in connections:
                if s < len(pts) and e < len(pts):
                    cv2.line(frame, pts[s], pts[e], (0, 255, 0), 2)
            for pt in pts:
                cv2.circle(frame, pt, 4, (0, 0, 255), -1)

    def release(self):
        if self.use_tasks:
            if hasattr(self, 'detector'):
                self.detector.close()
        elif hasattr(self, 'hands'):
            self.hands.close()


