"""
Camera — OpenCV webcam capture wrapper.
Handles opening, reading, flipping, and releasing the camera feed.
"""
import cv2
import numpy as np
from config import CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_INDEX


class Camera:
    """Manages the webcam capture lifecycle."""

    def __init__(self, index=CAMERA_INDEX, width=CAMERA_WIDTH, height=CAMERA_HEIGHT):
        self.cap = cv2.VideoCapture(index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self._ready = self.cap.isOpened()
        if self._ready:
            actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.width = actual_w if actual_w > 0 else width
            self.height = actual_h if actual_h > 0 else height
        else:
            self.width = width
            self.height = height

    @property
    def is_ready(self):
        return self._ready

    def read(self):
        """Return the current frame (BGR, flipped horizontally) or None."""
        if not self._ready:
            return None
        ret, frame = self.cap.read()
        if not ret:
            return None
        # Mirror so it feels natural
        frame = cv2.flip(frame, 1)
        return frame

    def release(self):
        if self.cap:
            self.cap.release()

    def __del__(self):
        self.release()
