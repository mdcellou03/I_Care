
from pathlib import Path
from fastai.vision.all import load_learner
from recommendation import get_recommendation
import json
import sys

# Find the model relative to this script
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "eye_model.pkl"

# Load trained model once
learn = load_learner(MODEL_PATH, cpu=True)


def predict_eye(image_path):
    """Predict an eye image's class using the trained model."""

    image_path = Path(image_path)

    if not image_path.is_file():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    # Run inference
    prediction, index, probabilities = learn.predict(
        image_path
    )

    # Convert scores to Python floats
    scores = {
        str(label): round(float(score), 4)
        for label, score in zip(
            learn.dls.vocab, probabilities
        )
    }

    pred_class = str(prediction)
    confidence = float(probabilities[index])

    return {
        "prediction": pred_class,
        "confidence": round(confidence, 4),
        "scores": scores,
        "recommendations": get_recommendation(pred_class),
        "disclaimer": (
            "I_Care is an experimental educational tool. "
            "Results are not a medical diagnosis or prescription."
        )
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python predict.py <image_path>")
        sys.exit(1)

    result = predict_eye(sys.argv[1])

    print(json.dumps(result, indent=2))
