"""Wraps the trained fastai model.

This is the only backend file that touches ML code, so changes on the ML side
should only ever need edits here.
"""

import sys
from functools import lru_cache

import numpy as np
from fastai.vision.all import load_learner
from PIL import Image

from app.config import MODEL_PATH, REQUIRED_PYTHON


@lru_cache(maxsize=1)
def get_learner():
    """Load the exported model once and reuse it for every request."""
    # Fail with a clear message instead of fastai's confusing unpickling errors.
    if sys.version_info[:2] != REQUIRED_PYTHON:
        raise RuntimeError(
            f"The model needs Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}, but this is "
            f"Python {sys.version.split()[0]}. Recreate backend/.venv with the right version."
        )
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

    return load_learner(MODEL_PATH, cpu=True)


def predict(image: Image.Image) -> dict:
    """Run one in-memory image through the model.

    Returns the top label, its probability, and the probability for every class.
    """
    learn = get_learner()

    # Pass a numpy array so the upload never has to be written to disk
    # (ml/predict.py works on file paths, which would force us to save one).
    with learn.no_bar():
        label, _, probs = learn.predict(np.asarray(image.convert("RGB")))

    # vocab is the model's own class list, so retrained classes show up here automatically.
    scores = {str(c): round(float(p), 4) for c, p in zip(learn.dls.vocab, probs)}
    return {"label": str(label), "confidence": scores[str(label)], "scores": scores}