"""Shared settings for the EyeCheck backend: paths, upload limits and user-facing text."""

from pathlib import Path

# config.py is in backend/app/, so parents[2] is the repo root (I_Care/)
REPO_ROOT = Path(__file__).resolve().parents[2]
ML_DIR = REPO_ROOT / "ml"
MODEL_PATH = REPO_ROOT / "ml" / "models" / "eye_model.pkl"

# The model is a pickle exported by the ML side on Python 3.13; it only loads on the same minor version.
REQUIRED_PYTHON = (3, 13)

# Phone photos are usually 2-8 MB; this leaves headroom without accepting anything.
MAX_UPLOAD_MB = 15
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

# Phone photos can be 4000px+ wide; the model only needs 224px, so shrink early to keep checks fast.
MAX_IMAGE_SIDE = 1024

# Below this, the UI shows the result as uncertain and suggests retaking the photo.
LOW_CONFIDENCE_THRESHOLD = 0.6

# Frontend origins allowed to call the API from a browser.
# Add e.g. "http://192.168.1.23:3000" when opening the frontend from a phone on the same Wi-Fi.
ALLOWED_ORIGINS = ["http://localhost:3000"]

DISCLAIMER = (
    "This is an experimental result from a student prototype, not a medical diagnosis. "
    "If you have concerns about your eyes or health, please see an eye-care professional."
)