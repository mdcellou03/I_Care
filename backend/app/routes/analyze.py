"""The analyze endpoint: receives an eye photo (uploaded or taken with the camera)
and returns the model's prediction.

Uploads are only held in memory for the length of the request. Nothing is saved.
"""

import io

from fastapi import APIRouter, File, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

from app.config import (
    DISCLAIMER,
    LOW_CONFIDENCE_THRESHOLD,
    MAX_IMAGE_SIDE,
    MAX_UPLOAD_BYTES,
    MAX_UPLOAD_MB,
)
from app.errors import ApiError
from app.schemas import AnalyzeResponse
from app.services import framing, predictor

# Teaches Pillow to open HEIC/HEIF, the default photo format on iPhones.
register_heif_opener()
router = APIRouter(prefix="/api/v1", tags=["analysis"])

# Specific advice for each reason ml/validate_image.py can return.
RETAKE_TIPS = {
    "Image resolution is too low": "Move closer to the eye or use your phone's main camera.",
    "Image is too dark": "Move somewhere brighter with even light.",
    "Image is too bright": "Avoid direct sunlight and turn off the flash.",
    "Image is too blurry": "Hold the phone steady and tap the eye to focus.",
}

FRAMING_MESSAGES = {
    "multiple_people": "We found more than one person. Please photograph one eye of one person.",
    "no_eye_found": "We couldn't find an eye. Take a close-up of one eye so it fills most of the photo.",
    "too_far": "You're too far away. Move closer so one eye fills most of the photo.",
}

def load_image(data: bytes) -> Image.Image:
    """Decode uploaded bytes into an upright, RGB, reasonably sized image."""
    try:
        image = Image.open(io.BytesIO(data))
        image.load()  # open() is lazy; load() forces a full decode so corrupt files fail here
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        # `from exc` keeps the original decoding error attached for debugging.
        raise ApiError(
            400, "invalid_image", "We couldn't read that file. Please upload a JPEG, PNG or HEIC photo."
        ) from exc
    # Phones often store photos sideways plus an EXIF "rotate me" tag; apply it so the eye is upright.
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")  # drops PNG transparency and handles greyscale
    image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))  # shrinks in place, keeps the aspect ratio
    return image


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(file: UploadFile = File(...)) -> AnalyzeResponse:
    """Validate the uploaded image, run it through the model and return the result."""
    # Plain `def`, not `async def`: FastAPI runs sync endpoints in a thread pool,
    # so CPU-heavy inference doesn't freeze the server for other requests.

    # Read one byte past the limit: enough to detect "too big" without loading a huge file.
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if not data:
        raise ApiError(400, "empty_file", "The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ApiError(413, "file_too_large", f"Please upload an image under {MAX_UPLOAD_MB} MB.")

    image = load_image(data)

    # Turn away photos the model can't judge fairly instead of returning a misleading result.
    quality = predictor.check_quality(image)
    if not quality["valid"]:
        reason = quality["reason"]
        tip = RETAKE_TIPS.get(reason, "Please retake the photo.")
        raise ApiError(422, "poor_quality", f"{reason}. {tip}")

    # The model labels anything as one of its classes, so check there's one person's eye first.
    problem = framing.check_framing(image)
    if problem:
        raise ApiError(422, problem, FRAMING_MESSAGES[problem])

    # The model was trained on eye close-ups, so give it the eye region rather than a whole face.
    result = predictor.predict(framing.crop_to_eyes(image))
    return AnalyzeResponse(
        predicted_class=result["label"],
        confidence=result["confidence"],
        scores=result["scores"],
        low_confidence=result["confidence"] < LOW_CONFIDENCE_THRESHOLD,
        recommendation=result["recommendation"],
        disclaimer=DISCLAIMER,
    )