
from pathlib import Path
from fastai.vision.all import load_learner
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    accuracy_score
)
from PIL import Image
import matplotlib.pyplot as plt
import pandas as pd
import torch

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "eye_model.pkl"
TEST_PATH = BASE_DIR / "data" / "processed" / "test"

# Load model
learn = load_learner(MODEL_PATH, cpu=True)
classes = list(learn.dls.vocab)

print("Classes:", classes)

# Collect test images
extensions = {".jpg", ".jpeg", ".png", ".webp"}
image_paths = [
    p for p in TEST_PATH.rglob("*")
    if p.is_file() and p.suffix.lower() in extensions
]

if not image_paths:
    raise RuntimeError("No test images found!")

y_true = []
y_pred = []
results = []

# Run inference
for i, path in enumerate(image_paths, 1):
    actual = path.parent.name

    if actual not in classes:
        raise ValueError(f"Unknown class: {actual}")

    prediction, index, probabilities = learn.predict(
        Image.open(path).convert("RGB")
    )

    predicted = str(prediction)
    confidence = float(probabilities[index])

    y_true.append(actual)
    y_pred.append(predicted)

    results.append({
        "image": str(path),
        "actual": actual,
        "predicted": predicted,
        "confidence": confidence,
        "correct": actual == predicted
    })

    if i % 20 == 0:
        print(f"Evaluated {i}/{len(image_paths)} images")

# Calculate accuracy
accuracy = accuracy_score(y_true, y_pred)
print(f"\nTest Accuracy: {accuracy:.2%}")

# Per-class metrics
print("\nClassification Report:")
print(classification_report(
    y_true,
    y_pred,
    labels=classes,
    zero_division=0
))

# Confusion matrix
cm = confusion_matrix(
    y_true,
    y_pred,
    labels=classes
)

ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=classes
).plot(cmap="Blues", values_format="d")

plt.title("I_Care - Test Confusion Matrix")
plt.tight_layout()

# Save evaluation results
OUTPUT_DIR = BASE_DIR / "evaluation"
OUTPUT_DIR.mkdir(exist_ok=True)

plt.savefig(
    OUTPUT_DIR / "confusion_matrix.png",
    dpi=150
)
plt.close()

df = pd.DataFrame(results)

df.to_csv(
    OUTPUT_DIR / "predictions.csv",
    index=False
)

# Show incorrect predictions
mistakes = df[~df["correct"]]

print(f"\nMisclassified images: {len(mistakes)}")
print(
    mistakes[["image", "actual", "predicted", "confidence"]]
    .head(15)
    .to_string(index=False)
)

print("\nEvaluation complete!")
print("Results saved in ml/evaluation/")