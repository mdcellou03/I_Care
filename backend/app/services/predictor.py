"""Wraps the ML code: the trained fastai model, plus the ML side's image quality
checks and recommendations.

This is the only backend file that touches ML code, so changes on the ML side
should only ever need edits here.
"""
import pathlib
import platform
import sys
from functools import lru_cache

import numpy as np
from fastai.vision.all import load_learner
from PIL import Image

from app.config import ML_DIR, MODEL_PATH, REQUIRED_PYTHON

# ml/ isn't pip-installed, so put its parent folder on the import path and import it
# as the `ml` package. Namespacing it avoids clashes with other modules called
# e.g. "recommendation".
sys.path.append(str(ML_DIR.parent))
from ml.recommendation import get_recommendation  # noqa: E402
from ml.validate_image import check_image_quality  # noqa: E402

@lru_cache(maxsize=1)
def get_learner():
    """Load the exported model once and reuse it for every request."""
    # Fail with a clear message instead of fastai's confusing unpickling errors.

    if sys.version_info[:2] != REQUIRED_PYTHON:
        required = ".".join(map(str, REQUIRED_PYTHON))
        raise RuntimeError(
            f"The model needs Python {required}, but this is Python {platform.python_version()}. "
            "Recreate backend/.venv with the right version."
        )

    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
    
    # The model was exported on Windows, so its pickle stores paths as WindowsPath.
    # Linux (where we deploy) can't create those, so load them as PosixPath instead.
    # Python 3.13 pickles reference pathlib._local, so patch it there.
    if platform.system() != "Windows":
        pathlib._local.WindowsPath = pathlib.PosixPath   

    return load_learner(MODEL_PATH, cpu=True)


def check_quality(image: Image.Image) -> dict:
    """Run the ML side's resolution/brightness/blur checks on an RGB image.

    Returns {"valid": bool, "reason": str | None, "checks": {...}}.
    """
    # OpenCV expects BGR channel order and PIL gives RGB, so flip the colour axis.
    bgr = np.ascontiguousarray(np.asarray(image)[:, :, ::-1])
    return check_image_quality(bgr)


def predict(image: Image.Image) -> dict:
    """Run one in-memory RGB image through the model.

    Returns the top label, its probability, the probability for every class,
    and the educational recommendation for that label.
    """
    learn = get_learner()

    # Pass a numpy array so the upload never has to be written to disk
    # (ml/predict.py works on file paths, which would force us to save one).
    with learn.no_bar():
        label, _, probs = learn.predict(np.asarray(image))

    # vocab is the model's own class list, so retrained classes show up here automatically.
    scores = {str(c): round(float(p), 4) for c, p in zip(learn.dls.vocab, probs)}
    label = str(label)
    return {
        "label": label,
        "confidence": scores[label],
        "scores": scores,
        "recommendation": get_recommendation(label),
    }