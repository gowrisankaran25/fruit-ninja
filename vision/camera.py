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
        self.width = width
        self.height = height
        self._ready = self.cap.isOpened()

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
