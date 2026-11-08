"""The analyze endpoint: receives an eye photo and returns the model's prediction.

Uploads are only held in memory for the length of the request. Nothing is saved.
"""

import io

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.config import DISCLAIMER, MAX_UPLOAD_BYTES, MAX_UPLOAD_MB
from app.schemas import AnalyzeResponse
from app.services import predictor

router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(file: UploadFile = File(...)) -> AnalyzeResponse:
    """Validate the uploaded image, run it through the model and return the result."""
    # Plain `def`, not `async def`: FastAPI runs sync endpoints in a thread pool,
    # so CPU-heavy inference doesn't freeze the server for other requests.

    # Read one byte past the limit: enough to detect "too big" without loading a huge file.
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"Image must be under {MAX_UPLOAD_MB} MB.")

    try:
        image = Image.open(io.BytesIO(data))
        image.load()  # open() is lazy; load() forces a full decode so corrupt files fail here
    except (UnidentifiedImageError, OSError):
        raise HTTPException(400, "Could not read the file as an image.")

    result = predictor.predict(image)
    return AnalyzeResponse(
        predicted_class=result["label"],
        confidence=result["confidence"],
        scores=result["scores"],
        disclaimer=DISCLAIMER,
    )