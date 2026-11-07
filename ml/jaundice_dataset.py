"""Download the dataset once and save a local Hugging Face DatasetDict copy.

Run from the ml directory with: python jaundice_dataset.py
Afterward, run preprocess.py to create the FastAI train/valid/test folders.
"""

from collections import Counter
from pathlib import Path

from datasets import load_dataset, load_from_disk


DATASET_ID = "Bleachcarte/Jaundice_Dataset"
DATASET_DIR = Path("data/jaundice_dataset")


try:
    # Reuse the local saved dataset when it is already available and valid.
    dataset = load_from_disk(str(DATASET_DIR))
    print(f"Loaded local dataset from {DATASET_DIR}")
except (FileNotFoundError, ValueError):
    # The folder may exist as an empty placeholder; in that case fetch the source.
    # Download from Hugging Face; no manual browser download is needed.
    dataset = load_dataset(DATASET_ID)
    DATASET_DIR.parent.mkdir(parents=True, exist_ok=True)
    dataset.save_to_disk(str(DATASET_DIR))
    print(f"Downloaded and saved dataset to {DATASET_DIR}")

# Show the split sizes and actual class counts so you can confirm what was saved.
label_names = dataset["train"].features["label"].names
print(f"Classes: {', '.join(label_names)}")
for split_name, split in dataset.items():
    counts = Counter(label_names[label_id] for label_id in split["label"])
    print(f"{split_name}: {len(split)} images — {dict(counts)}")
