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

# A face narrower than this share of the photo means the eyes are too small to crop reliably.
MIN_FACE_WIDTH_RATIO = 0.25


def check_framing(image: Image.Image) -> str | None:
    """Return "too_far" or "no_eye_found" if the photo can't be used, else None."""
    gray = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)
    width = gray.shape[1]

    faces = _FACE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(width // 12, width // 12))

    # A whole face is visible, so judge distance by how much of the photo the largest
    # face fills. (Close-ups can produce extra overlapping "faces", so we don't count them;
    # group photos still fail here because each face is small.)
    if len(faces):
        largest_face_width = max(w for (_, _, w, _) in faces)
        return "too_far" if largest_face_width / width < MIN_FACE_WIDTH_RATIO else None

    # No whole face: expected for a real close-up, but there must be at least one eye.
    # minSize is relative to the photo, so a tiny, far-away eye doesn't count.
    eyes = _EYE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(width // 15, width // 15))
    return None if len(eyes) else "no_eye_found"


def crop_to_eyes(image: Image.Image) -> Image.Image:
    """If a whole face is visible, crop to the eye region before prediction.

    The model was trained mostly on close-ups of eyes; given a whole face it reacts to
    skin and background (a clear selfie scored "Jaundice", the same eyes cropped scored
    "Healthy"). Close-ups with no detectable face are returned unchanged.
    """
    gray = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)
    height, width = gray.shape
    faces = _FACE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(width // 12, width // 12))
    if not len(faces):
        return image

    x, y, w, h = max(faces, key=lambda face: face[2])
    # Eyes sit in a band roughly 20-55% of the way down a detected face box.
    band_top, band_bottom = y + h // 5, y + h * 11 // 20
    eyes = _EYE.detectMultiScale(gray[band_top:band_bottom, x:x + w], scaleFactor=1.1, minNeighbors=5, minSize=(w // 8, w // 8))

    if len(eyes):
        # Box around all detected eyes (coordinates are relative to the band), plus a margin.
        pad = w // 10
        left = x + min(ex for ex, _, _, _ in eyes) - pad
        right = x + max(ex + ew for ex, _, ew, _ in eyes) + pad
        top = band_top + min(ey for _, ey, _, _ in eyes) - pad
        bottom = band_top + max(ey + eh for _, ey, _, eh in eyes) + pad
    else:
        left, right, top, bottom = x, x + w, band_top, band_bottom

    return image.crop((max(0, left), max(0, top), min(width, right), min(height, bottom)))