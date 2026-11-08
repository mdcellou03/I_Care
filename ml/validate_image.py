
from pathlib import Path
import json
import sys

import cv2
import numpy as np


# ==========================================
# CONFIGURATION
# ==========================================

MIN_WIDTH = 160
MIN_HEIGHT = 160

MIN_BRIGHTNESS = 35
MAX_BRIGHTNESS = 225

MIN_BLUR_SCORE = 40

# These thresholds are experimental.
# They are not medical image quality standards.


# ==========================================
# IMAGE QUALITY CHECKS
# ==========================================

def check_image_quality(image):
    """
    Check image resolution, brightness and blur.
    """

    height, width = image.shape[:2]

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    brightness = float(np.mean(gray))

    blur_score = float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()
    )

    checks = {
        "width": width,
        "height": height,
        "brightness": round(brightness, 2),
        "blur_score": round(blur_score, 2)
    }

    if width < MIN_WIDTH or height < MIN_HEIGHT:
        return {
            "valid": False,
            "reason": "Image resolution is too low",
            "checks": checks
        }

    if brightness < MIN_BRIGHTNESS:
        return {
            "valid": False,
            "reason": "Image is too dark",
            "checks": checks
        }

    if brightness > MAX_BRIGHTNESS:
        return {
            "valid": False,
            "reason": "Image is too bright",
            "checks": checks
        }

    if blur_score < MIN_BLUR_SCORE:
        return {
            "valid": False,
            "reason": "Image is too blurry",
            "checks": checks
        }

    return {
        "valid": True,
        "reason": None,
        "checks": checks
    }


# ==========================================
# MAIN VALIDATION FUNCTION
# ==========================================

def validate_image(image_path):
    """
    Validate image quality before prediction.

    Called by the backend.

    Returns:
        {
            "valid": bool,
            "reason": str or None,
            "checks": dict
        }
    """

    path = Path(image_path)

    if not path.is_file():
        return {
            "valid": False,
            "reason": "Image file not found",
            "checks": {}
        }

    image = cv2.imread(str(path))

    if image is None:
        return {
            "valid": False,
            "reason": "Invalid or unreadable image",
            "checks": {}
        }

    return check_image_quality(image)


# ==========================================
# COMMAND LINE TESTING
# ==========================================

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(
            "Usage: python validate_image.py <image_path>"
        )
        sys.exit(1)

    result = validate_image(sys.argv[1])

    print(json.dumps(result, indent=2))