"""Extract the Uveitis class from the cached/downloaded Orvile Kaggle dataset.

Run from I_Care/ml with: python uveitis.py
The selected images are copied into data/uveitis_images/Uveitis/.
"""

from datetime import datetime
from hashlib import sha256
from pathlib import Path
import os
import shutil

import kagglehub
from PIL import Image


ML_DIR = Path(__file__).resolve().parent
DATA_DIR = ML_DIR / "data"
OUTPUT_DIR = DATA_DIR / "uveitis_images"
OUTPUT_CLASS_DIR = OUTPUT_DIR / "Uveitis"
DATASET_HANDLE = "orvile/eye-diseases-classification"
DATASET_SUBPATH = (
    "Image Dataset on Eye Diseases Classification "
    "(Uveitis, Conjunctivitis, Cataract, Eyelid) with Symptoms and SMOTE Validation/Uveitis"
)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def cached_source_folder() -> Path | None:
    """Use the locally cached dataset version when available."""
    owner, slug = DATASET_HANDLE.split("/", maxsplit=1)
    cache_root = Path(
        os.environ.get("KAGGLEHUB_CACHE", str(Path.home() / ".cache" / "kagglehub"))
    )
    versions_dir = cache_root / "datasets" / owner / slug / "versions"
    if not versions_dir.is_dir():
        return None

    versions = sorted(
        (path for path in versions_dir.iterdir() if path.is_dir()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for version_dir in versions:
        direct = version_dir / DATASET_SUBPATH
        if direct.is_dir():
            return direct
        matches = [
            path for path in version_dir.rglob("*")
            if path.is_dir() and path.name.casefold() == "uveitis"
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise RuntimeError(
                "Found multiple Uveitis folders in the cached Kaggle dataset: "
                + ", ".join(str(path) for path in matches)
            )
    return None


def download_source_folder() -> Path:
    """Download only Uveitis when possible; otherwise find it in the full dataset."""
    cached = cached_source_folder()
    if cached is not None:
        print(f"Using cached Uveitis folder: {cached}")
        return cached

    try:
        selected = Path(kagglehub.dataset_download(DATASET_HANDLE, path=DATASET_SUBPATH))
        if selected.is_dir():
            return selected
    except Exception as error:
        response = getattr(error, "response", None)
        if getattr(response, "status_code", None) != 404:
            raise
        print("Kaggle returned 404 for the selected folder; retrying with the full dataset.")

    dataset_root = Path(kagglehub.dataset_download(DATASET_HANDLE))
    matches = [
        path for path in dataset_root.rglob("*")
        if path.is_dir() and path.name.casefold() == "uveitis"
    ]
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected one Uveitis folder in {dataset_root}, found {len(matches)}: {matches}"
        )
    return matches[0]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="replace the extracted Uveitis folder while preserving a backup",
    )
    args = parser.parse_args()

    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()) and not args.rebuild:
        raise FileExistsError(
            f"{OUTPUT_DIR} already contains images. Use `python uveitis.py --rebuild` to refresh it."
        )

    source_dir = download_source_folder()
    staged_dir = DATA_DIR / f"uveitis_build_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    staged_class_dir = staged_dir / "Uveitis"
    staged_class_dir.mkdir(parents=True, exist_ok=True)

    copied_hashes = set()
    unreadable = 0
    duplicate_count = 0
    image_count = 0
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

        image_count += 1
        if digest in copied_hashes:
            duplicate_count += 1
            continue
        copied_hashes.add(digest)
        shutil.copy2(
            image_path,
            staged_class_dir / f"{digest[:20]}{image_path.suffix.lower()}",
        )

    if image_count == 0:
        shutil.rmtree(staged_dir)
        raise ValueError(f"No readable Uveitis images found in {source_dir}.")

    backup_dir = None
    if OUTPUT_DIR.exists():
        if OUTPUT_DIR.resolve().parent != DATA_DIR.resolve() or staged_dir.resolve().parent != DATA_DIR.resolve():
            shutil.rmtree(staged_dir)
            raise RuntimeError("Refusing to move image folders outside ml/data.")
        backup_dir = DATA_DIR / f"uveitis_images_backup_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        shutil.move(str(OUTPUT_DIR), str(backup_dir))
    try:
        shutil.move(str(staged_dir), str(OUTPUT_DIR))
    except Exception:
        if backup_dir is not None and backup_dir.exists() and not OUTPUT_DIR.exists():
            shutil.move(str(backup_dir), str(OUTPUT_DIR))
        raise

    print(f"Output: {OUTPUT_CLASS_DIR}")
    print(f"Readable Uveitis images: {image_count}")
    print(f"Unique files copied: {len(copied_hashes)}")
    print(f"Exact duplicate files skipped: {duplicate_count}")
    print(f"Unreadable images skipped: {unreadable}")


if __name__ == "__main__":
    main()
