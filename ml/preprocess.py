"""Combine the jaundice, cataract, conjunctivitis, and uveitis sources into FastAI splits.

From I_Care/ml, run:
    python cataract.py
    python conjunctivitis.py
    python uveitis.py
    python preprocess.py --rebuild

The output is data/processed/{train,valid,test}/{Healthy,Jaundice,Cataract,Conjunctivitis,Uveitis}/.
"""

import argparse
from collections import Counter, defaultdict
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import shutil

from datasets import load_dataset, load_from_disk
from PIL import Image
from sklearn.model_selection import train_test_split


ML_DIR = Path(__file__).resolve().parent
SEED = 42
DATASET_DIR = ML_DIR / "data" / "jaundice_dataset"
DATASET_ID = "Bleachcarte/Jaundice_Dataset"
CATARACT_DIR = ML_DIR / "data" / "cataract_images"
CONJUNCTIVITIS_DIR = ML_DIR / "data" / "conjunctivitis_images" / "Conjunctivitis"
UVEITIS_DIR = ML_DIR / "data" / "uveitis_images" / "Uveitis"
OUTPUT_DIR = ML_DIR / "data" / "processed"
CLASS_NAMES = ("Healthy", "Jaundice", "Cataract", "Conjunctivitis", "Uveitis")
SPLIT_RATIOS = {"train": 0.70, "valid": 0.15, "test": 0.15}


def image_fingerprint(image: Image.Image) -> str:
    """Hash decoded pixels so visually identical copies stay in one split."""
    rgb = image.convert("RGB")
    content = f"{rgb.width}x{rgb.height}:".encode("ascii") + rgb.tobytes()
    return sha256(content).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="replace the generated data/processed folder with fresh splits",
    )
    args = parser.parse_args()

    # Build beside the current output. This lets Windows/OneDrive swap folders
    # without deleting the existing export first.
    build_dir = ML_DIR / "data" / f"processed_build_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()) and not args.rebuild:
        raise FileExistsError(
            f"{OUTPUT_DIR} already contains an export. Use `--rebuild` to replace it safely."
        )

    # Use the local Hugging Face copy when present; download it if missing or invalid.
    try:
        jaundice_data = load_from_disk(str(DATASET_DIR))
    except (FileNotFoundError, ValueError):
        jaundice_data = load_dataset(DATASET_ID)
        DATASET_DIR.parent.mkdir(parents=True, exist_ok=True)
        jaundice_data.save_to_disk(str(DATASET_DIR))

    # Require the cataract extraction step so a run cannot silently omit that class.
    required_cataract_classes = ("Healthy", "Cataract")
    missing = [name for name in required_cataract_classes if not (CATARACT_DIR / name).is_dir()]
    if missing:
        raise FileNotFoundError(
            f"Missing {', '.join(missing)} under {CATARACT_DIR}. "
            "Run `python cataract.py` first."
        )
    if not CONJUNCTIVITIS_DIR.is_dir():
        raise FileNotFoundError(
            f"Missing {CONJUNCTIVITIS_DIR}. Run `python conjunctivitis.py` first."
        )
    if not UVEITIS_DIR.is_dir():
        raise FileNotFoundError(
            f"Missing {UVEITIS_DIR}. Run `python uveitis.py` first."
        )

    # Accumulate unique images by decoded pixels. This catches exact duplicates across
    # both sources and prevents them from leaking between train/valid/test.
    unique_images = {}
    unreadable_count = 0
    duplicate_count = 0

    def add_image(image: Image.Image, label: str, source: str) -> None:
        nonlocal unreadable_count, duplicate_count
        try:
            image = image.convert("RGB")
            fingerprint = image_fingerprint(image)
        except Exception as error:
            unreadable_count += 1
            print(f"Skipping unreadable image from {source}: {error}")
            return

        previous = unique_images.get(fingerprint)
        if previous is not None:
            if previous["label"] != label:
                raise ValueError(
                    "Identical image pixels have conflicting labels "
                    f"{previous['label']} and {label} (source: {source}). Review the labels."
                )
            duplicate_count += 1
            return
        unique_images[fingerprint] = {"image": image, "label": label}

    # Add the Healthy and Jaundice examples from the Hugging Face source.
    source_label_names = jaundice_data["train"].features["label"].names
    for source_split in jaundice_data:
        for row_index, row in enumerate(jaundice_data[source_split]):
            try:
                label = source_label_names[int(row["label"])]
            except Exception as error:
                unreadable_count += 1
                print(f"Skipping unreadable jaundice row {source_split}/{row_index}: {error}")
                continue
            add_image(row["image"], label, f"jaundice {source_split} row {row_index}")

    # Kaggle's Normal examples were mapped to Healthy by cataract.py. Add those and
    # Cataract examples so all three labels share one training dataset.
    for label in required_cataract_classes:
        class_dir = CATARACT_DIR / label
        image_paths = [path for path in class_dir.rglob("*") if path.is_file()]
        if not image_paths:
            raise ValueError(f"No extracted image files found in {class_dir}.")
        for image_path in image_paths:
            try:
                with Image.open(image_path) as image:
                    image = image.copy()
            except Exception as error:
                unreadable_count += 1
                print(f"Skipping unreadable image {image_path}: {error}")
                continue
            add_image(image, label, str(image_path))

    conjunctivitis_paths = [
        path for path in CONJUNCTIVITIS_DIR.rglob("*")
        if path.is_file()
    ]
    if not conjunctivitis_paths:
        raise ValueError(f"No extracted image files found in {CONJUNCTIVITIS_DIR}.")
    for image_path in conjunctivitis_paths:
        try:
            with Image.open(image_path) as image:
                image = image.copy()
        except Exception as error:
            unreadable_count += 1
            print(f"Skipping unreadable image {image_path}: {error}")
            continue
        add_image(image, "Conjunctivitis", str(image_path))

    uveitis_paths = [
        path for path in UVEITIS_DIR.rglob("*")
        if path.is_file()
    ]
    if not uveitis_paths:
        raise ValueError(f"No extracted image files found in {UVEITIS_DIR}.")
    for image_path in uveitis_paths:
        try:
            with Image.open(image_path) as image:
                image = image.copy()
        except Exception as error:
            unreadable_count += 1
            print(f"Skipping unreadable image {image_path}: {error}")
            continue
        add_image(image, "Uveitis", str(image_path))

    # Split each class independently with a fixed seed. No patient IDs are provided,
    # so the best available leakage check is grouping exact duplicate pixel images.
    groups_by_label = defaultdict(list)
    for fingerprint, item in unique_images.items():
        groups_by_label[item["label"]].append(fingerprint)

    assigned = {split: [] for split in SPLIT_RATIOS}
    for label in CLASS_NAMES:
        fingerprints = sorted(groups_by_label[label])
        if len(fingerprints) < 3:
            raise ValueError(
                f"Only {len(fingerprints)} unique images were found for {label}; "
                "at least three are required for train/valid/test splits."
            )
        train_and_valid, test = train_test_split(
            fingerprints,
            test_size=SPLIT_RATIOS["test"],
            random_state=SEED,
        )
        train, valid = train_test_split(
            train_and_valid,
            test_size=SPLIT_RATIOS["valid"] / (1 - SPLIT_RATIOS["test"]),
            random_state=SEED,
        )
        assigned["train"].extend(train)
        assigned["valid"].extend(valid)
        assigned["test"].extend(test)

    counts = {split: Counter() for split in assigned}
    for split, fingerprints in assigned.items():
        for fingerprint in fingerprints:
            item = unique_images[fingerprint]
            destination = build_dir / split / item["label"]
            destination.mkdir(parents=True, exist_ok=True)
            item["image"].save(destination / f"{fingerprint[:16]}.jpg", format="JPEG", quality=95)
            counts[split][item["label"]] += 1

    # Keep the previous output as a local backup, then move the finished build into place.
    backup_dir = None
    if OUTPUT_DIR.exists():
        data_root = (ML_DIR / "data").resolve()
        if OUTPUT_DIR.resolve().parent != data_root or build_dir.resolve().parent != data_root:
            raise RuntimeError("Refusing to move dataset folders outside ml/data.")
        backup_dir = data_root / f"processed_backup_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        shutil.move(str(OUTPUT_DIR), str(backup_dir))
    try:
        shutil.move(str(build_dir), str(OUTPUT_DIR))
    except Exception:
        if backup_dir is not None and backup_dir.exists() and not OUTPUT_DIR.exists():
            shutil.move(str(backup_dir), str(OUTPUT_DIR))
        raise

    print(f"\nOutput: {OUTPUT_DIR}")
    print(f"Classes: {', '.join(CLASS_NAMES)}")
    print(f"Unreadable images skipped: {unreadable_count}")
    print(f"Exact duplicate copies grouped: {duplicate_count}")
    print("\nExported counts:")
    for split in ("train", "valid", "test"):
        total = sum(counts[split].values())
        detail = ", ".join(f"{label}: {counts[split][label]}" for label in CLASS_NAMES)
        print(f"  {split}: {total} ({detail})")
    print("\nNo patient IDs were provided; exact pixel duplicates are grouped, but near-duplicates may remain.")


if __name__ == "__main__":
    main()
