"""Framing check: makes sure the photo is a close-up of one person's eye before we run the model.

The classifier always picks one of its six labels, even for photos that aren't eyes
(random noise scored 70% "Jaundice" in our tests), so we gate it with OpenCV's
built-in face and eye detectors. They ship with opencv-python 4.x, so there's no
extra model to download.
"""

import cv2
import numpy as np
from PIL import Image

_FACE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
_EYE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")

# A face narrower than this share of the photo means the eyes are too small for the model.
MIN_FACE_WIDTH_RATIO = 0.5


def check_framing(image: Image.Image) -> str | None:
    """Return "multiple_people", "too_far" or "no_eye_found" if the photo can't be used, else None."""
    gray = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)
    width = gray.shape[1]

    faces = _FACE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(width // 12, width // 12))
    if len(faces) > 1:
        return "multiple_people"

    # A whole face is visible, so judge distance by how much of the photo it fills.
    # (Counting eyes here is unreliable: patterns, nostrils and mouths cause false "eyes".)
    if len(faces) == 1:
        face_width = faces[0][2]
        return "too_far" if face_width / width < MIN_FACE_WIDTH_RATIO else None

    # No whole face: expected for a real close-up, but there must be at least one eye.
    # minSize is relative to the photo, so a tiny, far-away eye doesn't count.
    eyes = _EYE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(width // 15, width // 15))
    return None if len(eyes) else "no_eye_found"