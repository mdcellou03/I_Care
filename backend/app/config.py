"""Shared settings for the EyeCheck backend: paths, upload limits and user-facing text.

Paths and allowed origins can be overridden with environment variables (or a
backend/.env file), so the same code runs locally and when deployed.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads backend/.env if it exists; real environment variables take priority

# Default repo layout: this file is backend/app/config.py, so parents[2] is the repo root.
_DEFAULT_ML_DIR = Path(__file__).resolve().parents[2] / "ml"

# Where the ML code and model live. Override when deploying with a different folder layout.
ML_DIR = Path(os.getenv("EYECHECK_ML_DIR", _DEFAULT_ML_DIR)).resolve()
MODEL_PATH = Path(os.getenv("EYECHECK_MODEL_PATH", ML_DIR / "models" / "eye_model.pkl")).resolve()

# The model is a pickle exported by the ML side on Python 3.13; it only loads on the same minor version.
REQUIRED_PYTHON = (3, 13)

# Phone photos are usually 2-8 MB; this leaves headroom without accepting anything.
MAX_UPLOAD_MB = 15
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

# Phone photos can be 4000px+ wide; the model only needs 224px, so shrink early to keep checks fast.
MAX_IMAGE_SIDE = 1024

# Below this, the UI shows the result as uncertain and suggests retaking the photo.
LOW_CONFIDENCE_THRESHOLD = 0.6

# Comma-separated frontend origins allowed to call the API from a browser,
# e.g. EYECHECK_ALLOWED_ORIGINS="http://localhost:3000,https://eyecheck.vercel.app"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("EYECHECK_ALLOWED_ORIGINS", "http://localhost:5500").split(",")
    if origin.strip()
]

DISCLAIMER = (
    "This is an experimental result from a student prototype, not a medical diagnosis. "
    "If you have concerns about your eyes or health, please see an eye-care professional."
)