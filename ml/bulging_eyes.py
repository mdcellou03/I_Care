"""Extract the Bulging_Eyes folder from the Kaggle eye-disease dataset.

From I_Care/ml, run ``python bulging_eyes.py``. The selected images are copied
to data/bulging_eyes_images/Bulging_Eyes for the preprocessing script.
"""

from collections import Counter
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import argparse
import shutil

import kagglehub
from PIL import Image


DATASET_HANDLE = "mohamedsayed12/eye-disease-dataset"
SOURCE_FOLDER = "Bulging_Eyes"
ML_DIR = Path(__file__).resolve().parent
DATA_DIR = ML_DIR / "data"
OUTPUT_DIR = DATA_DIR / "bulging_eyes_images"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def find_source_folder(dataset_root: Path) -> Path:
    """Locate the dataset's Bulging_Eyes directory, regardless of letter case."""
    matches = [
        path for path in dataset_root.rglob("*")
        if path.is_dir() and path.name.casefold() == SOURCE_FOLDER.casefold()
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(
            f"Found multiple {SOURCE_FOLDER} folders in {dataset_root}: "
            + ", ".join(str(path) for path in matches)
        )
    top_level = [path.name for path in dataset_root.iterdir()]
    raise FileNotFoundError(
        f"Could not find the {SOURCE_FOLDER!r} folder in {dataset_root}. "
        f"Top-level entries: {top_level}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="replace the extracted data/bulging_eyes_images folder",
    )
    args = parser.parse_args()

    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()) and not args.rebuild:
        raise FileExistsError(
            f"{OUTPUT_DIR} already has images. Run `python bulging_eyes.py --rebuild`."
        )

    dataset_root = Path(kagglehub.dataset_download(DATASET_HANDLE))
    if not dataset_root.exists():
        raise FileNotFoundError(f"KaggleHub returned a missing path: {dataset_root}")
    source_dir = find_source_folder(dataset_root)

    build_dir = DATA_DIR / f"bulging_eyes_images_build_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    counts = Counter()
    seen_hashes = set()
    unreadable = 0
    duplicate_count = 0

    try:
        for image_path in source_dir.rglob("*"):
            if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            try:
                with Image.open(image_path) as image:
                    image.verify()
                digest = sha256(image_path.read_bytes()).hexdigest()
            except Exception as error:
                unreadable += 1
                print(f"Skipping unreadable image {image_path}: {error}")
                continue

            if digest in seen_hashes:
                duplicate_count += 1
                continue
            seen_hashes.add(digest)

            destination_dir = build_dir / SOURCE_FOLDER
            destination_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(
                image_path,
                destination_dir / f"{digest[:20]}{image_path.suffix.lower()}",
            )
            counts[SOURCE_FOLDER] += 1

        if counts[SOURCE_FOLDER] == 0:
            raise ValueError(f"No readable supported image files found in {source_dir}.")

        backup_dir = None
        if OUTPUT_DIR.exists():
            if OUTPUT_DIR.resolve().parent != DATA_DIR.resolve():
                raise RuntimeError(f"Refusing to move unexpected directory: {OUTPUT_DIR}")
            backup_dir = DATA_DIR / f"bulging_eyes_images_backup_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
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

    print(f"Source: {source_dir}")
    print(f"Output: {OUTPUT_DIR / SOURCE_FOLDER}")
    print(f"Bulging_Eyes images copied: {counts[SOURCE_FOLDER]}")
    print(f"Unreadable images skipped: {unreadable}")
    print(f"Exact duplicate files skipped: {duplicate_count}")


if __name__ == "__main__":
    main()
