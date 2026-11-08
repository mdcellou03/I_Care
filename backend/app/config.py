"""Shared settings for the EyeCheck backend: paths, upload limits and user-facing text."""

from pathlib import Path

# config.py is in backend/app/, so parents[2] is the repo root (I_Care/)
REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = REPO_ROOT / "ml" / "models" / "eye_model.pkl"

# The model is a pickle exported by the ML side on Python 3.13; it only loads on the same minor version.
REQUIRED_PYTHON = (3, 13)

# Phone photos are usually 2-8 MB; this leaves headroom without accepting anything.
MAX_UPLOAD_MB = 15
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

DISCLAIMER = (
    "This is an experimental result from a student prototype, not a medical diagnosis. "
    "If you have concerns about your eyes or health, please see an eye-care professional."
)