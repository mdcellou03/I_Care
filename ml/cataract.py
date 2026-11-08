"""Collect the project cataract images from the two Kaggle sources.

Run from I_Care/ml with ``python cataract.py --rebuild``. The first source has
Healthy/Normal and Cataract folders; the second source contributes its
``processed_images/test/cataract`` folder to the existing Cataract class.
"""

from collections import Counter
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import argparse
import re
import shutil

import kagglehub
from PIL import Image


SOURCES = (
    {
        "handle": "nandanp6/cataract-image-dataset",
        "subpath": "processed_images",
        "mode": "class_folders",
    },
    {
        "handle": "hemooredaoo/cataract",
        "subpath": "processed_images/test/cataract",
        "mode": "cataract_only",
    },
)
ML_DIR = Path(__file__).resolve().parent
DATA_DIR = ML_DIR / "data"
OUTPUT_DIR = DATA_DIR / "cataract_images"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def find_subpath(root: Path, wanted: str) -> Path:
    """Find a selected Kaggle folder without depending on path capitalization."""
    parts = Path(wanted).parts
    candidates = [root]
    for part in parts:
        next_candidates = []
        for parent in candidates:
            if not parent.is_dir():
                continue
            next_candidates.extend(
                child for child in parent.iterdir()
                if child.is_dir() and child.name.casefold() == part.casefold()
            )
        candidates = next_candidates
    if candidates:
        return candidates[0]
    raise FileNotFoundError(f"Could not find {wanted!r} inside downloaded dataset {root}.")


def label_for_path(path: Path) -> str | None:
    """Map source folder names from the first Kaggle dataset to project classes."""
    tokens = {
        token
        for part in path.parts
        for token in re.split(r"[^a-z0-9]+", part.lower())
        if token
    }
    if "normal" in tokens or "healthy" in tokens:
        return "Healthy"
    if "cataract" in tokens and not ({"no", "non", "without"} & tokens):
        return "Cataract"
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rebuild", action="store_true", help="replace the extracted image folders")
    args = parser.parse_args()

    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()) and not args.rebuild:
        raise FileExistsError(f"{OUTPUT_DIR} already has images. Run `python cataract.py --rebuild`.")

    source_dirs = []
    for source in SOURCES:
        root = Path(kagglehub.dataset_download(source["handle"]))
        if not root.exists():
            raise FileNotFoundError(f"KaggleHub returned a missing path: {root}")
        source_dirs.append((source, find_subpath(root, source["subpath"])))

    build_dir = DATA_DIR / f"cataract_images_build_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    counts = Counter()
    unreadable = 0
    duplicate_count = 0
    seen = {}
    try:
        for source, source_dir in source_dirs:
            for image_path in source_dir.rglob("*"):
                if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                    continue
                if source["mode"] == "cataract_only":
                    label = "Cataract"
                else:
                    label = label_for_path(image_path.relative_to(source_dir))
                    if label is None:
                        continue
                try:
                    with Image.open(image_path) as image:
                        image.verify()
                    digest = sha256(image_path.read_bytes()).hexdigest()
                except Exception as error:
                    unreadable += 1
                    print(f"Skipping unreadable image {image_path}: {error}")
                    continue
                if digest in seen:
                    if seen[digest] != label:
                        raise ValueError(f"Duplicate image has conflicting labels: {seen[digest]} and {label}")
                    duplicate_count += 1
                    continue
                seen[digest] = label
                destination_dir = build_dir / label
                destination_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(image_path, destination_dir / f"{digest[:20]}{image_path.suffix.lower()}")
                counts[label] += 1

        if not counts["Healthy"] or not counts["Cataract"]:
            raise ValueError(f"Expected Healthy and Cataract images; extracted counts: {dict(counts)}")

        backup_dir = None
        if OUTPUT_DIR.exists():
            if OUTPUT_DIR.resolve().parent != DATA_DIR.resolve():
                raise RuntimeError(f"Refusing to move unexpected directory: {OUTPUT_DIR}")
            backup_dir = DATA_DIR / f"cataract_images_backup_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            shutil.move(str(OUTPUT_DIR), str(backup_dir))
        try:
            shutil.move(str(build_dir), str(OUTPUT_DIR))
        except Exception:
            if backup_dir and backup_dir.exists() and not OUTPUT_DIR.exists():
                shutil.move(str(backup_dir), str(OUTPUT_DIR))
            raise
    except Exception:
        if build_dir.exists():
            shutil.rmtree(build_dir)
        raise

    print(f"Output: {OUTPUT_DIR}")
    for label in ("Healthy", "Cataract"):
        print(f"{label}: {counts[label]}")
    print(f"Unreadable images skipped: {unreadable}")
    print(f"Exact duplicate files skipped: {duplicate_count}")
    for source, source_dir in source_dirs:
        print(f"Source {source['handle']} ({source['subpath']}): {source_dir}")


if __name__ == "__main__":
    main()
