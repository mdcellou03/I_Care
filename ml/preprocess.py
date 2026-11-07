"""Validate the saved eye image dataset and export FastAI folder splits.

Run from this directory with: python preprocess.py
The output is written to data/processed/{train,valid,test}/{class}/.
"""

from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

from datasets import load_dataset, load_from_disk
from PIL import Image
from sklearn.model_selection import train_test_split


SEED = 42
DATASET_DIR = Path("data/jaundice_dataset")
DATASET_ID = "Bleachcarte/Jaundice_Dataset"
OUTPUT_DIR = Path("data/processed")
SPLIT_RATIOS = {"train": 0.70, "valid": 0.15, "test": 0.15}


def image_fingerprint(image: Image.Image) -> str:
    """Hash decoded pixels so byte-different copies of the same image are grouped."""
    rgb = image.convert("RGB")
    content = f"{rgb.width}x{rgb.height}:".encode("ascii") + rgb.tobytes()
    return sha256(content).hexdigest()


def main() -> None:
    # Reuse the saved copy when present. Teammates without it can fetch the same
    # published dataset once; it is saved locally for later reruns.
    if DATASET_DIR.exists():
        dataset = load_from_disk(str(DATASET_DIR))
    else:
        dataset = load_dataset(DATASET_ID)
        DATASET_DIR.parent.mkdir(parents=True, exist_ok=True)
        dataset.save_to_disk(str(DATASET_DIR))
    label_names = dataset["train"].features["label"].names

    # Gather readable images from the dataset's original splits. Only image and label
    # fields exist here, so no patient IDs are available for patient-level grouping.
    unique_images = {}
    corrupt_count = 0
    duplicate_count = 0
    for original_split in dataset:
        for row_index, row in enumerate(dataset[original_split]):
            try:
                image = row["image"].convert("RGB")
                label_id = int(row["label"])
                fingerprint = image_fingerprint(image)
            except Exception as error:
                corrupt_count += 1
                print(f"Skipping unreadable image ({original_split} row {row_index}): {error}")
                continue

            label = label_names[label_id]
            existing = unique_images.get(fingerprint)
            if existing is not None:
                if existing["label"] != label:
                    raise ValueError(
                        "The same image pixels have conflicting labels: "
                        f"{existing['label']} and {label}. Review the source labels before training."
                    )
                duplicate_count += 1
                continue

            unique_images[fingerprint] = {"image": image, "label": label}

    # Split each class independently for reproducible, approximately stratified splits.
    # Fingerprints are the split units, so exact duplicate images cannot cross splits.
    groups_by_label = defaultdict(list)
    for fingerprint, item in unique_images.items():
        groups_by_label[item["label"]].append(fingerprint)

    assigned = {split: [] for split in SPLIT_RATIOS}
    for label in label_names:
        fingerprints = sorted(groups_by_label[label])
        if len(fingerprints) < 3:
            raise ValueError(f"Not enough unique images in class {label!r} to create three splits.")

        train_and_valid, test = train_test_split(
            fingerprints,
            test_size=SPLIT_RATIOS["test"],
            random_state=SEED,
        )
        # 0.15 of the whole class is 0.15 / 0.85 of the remainder.
        train, valid = train_test_split(
            train_and_valid,
            test_size=SPLIT_RATIOS["valid"] / (1 - SPLIT_RATIOS["test"]),
            random_state=SEED,
        )
        assigned["train"].extend(train)
        assigned["valid"].extend(valid)
        assigned["test"].extend(test)

    # Refuse to mix new output with an old export. Remove data/processed yourself
    # before rerunning if you intentionally want a fresh export.
    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()):
        raise FileExistsError(
            f"{OUTPUT_DIR} already contains files. Move or remove it before regenerating splits."
        )

    counts = {split: Counter() for split in assigned}
    for split, fingerprints in assigned.items():
        for fingerprint in fingerprints:
            item = unique_images[fingerprint]
            destination = OUTPUT_DIR / split / item["label"]
            destination.mkdir(parents=True, exist_ok=True)
            # Stable names make output reproducible with the fixed split seed.
            image_path = destination / f"{fingerprint[:16]}.jpg"
            item["image"].save(image_path, format="JPEG", quality=95)
            counts[split][item["label"]] += 1

    print(f"\nSource: {DATASET_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Classes: {', '.join(label_names)}")
    print(f"Unreadable images skipped: {corrupt_count}")
    print(f"Exact duplicate images grouped (extra copies): {duplicate_count}")
    print("\nExported counts:")
    for split in ("train", "valid", "test"):
        total = sum(counts[split].values())
        details = ", ".join(f"{label}: {counts[split][label]}" for label in label_names)
        print(f"  {split}: {total} ({details})")
    print("\nNo patient IDs were present; grouping only prevents exact-pixel duplicates crossing splits.")


if __name__ == "__main__":
    main()
