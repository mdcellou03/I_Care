"""Download two Kaggle folders and collect their conjunctivitis images.

Run from I_Care/ml with: python conjunctivitis.py
The selected images are copied into data/conjunctivitis_images/Conjunctivitis/.
"""

from collections import Counter
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import os
import shutil

import kagglehub
from PIL import Image


ML_DIR = Path(__file__).resolve().parent
DATA_DIR = ML_DIR / "data"
OUTPUT_DIR = DATA_DIR / "conjunctivitis_images"
OUTPUT_CLASS_DIR = OUTPUT_DIR / "Conjunctivitis"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}

# The Kaggle URL's selected dataset title is long; the actual class directory
# in the downloaded data is spelled "Conjunctivitis".
SOURCES = (
    {
        "name": "alisofiya",
        "handle": "alisofiya/conjunctivitis",
        "subpath": "Dataset/infected_eye",
    },
    {
        "name": "orvile",
        "handle": "orvile/eye-diseases-classification",
        "subpath": (
            "Image Dataset on Eye Diseases Classification "
            "(Uveitis, Conjunctivitis, Cataract, Eyelid) with Symptoms and SMOTE Validation/"
            "Conjunctivitis"
        ),
    },
)


def _http_status(error: Exception) -> int | None:
    """Read an HTTP status from KaggleHub's wrapped API errors when available."""
    response = getattr(error, "response", None)
    return getattr(response, "status_code", None)


def _find_selected_folder(dataset_root: Path, subpath: str) -> Path:
    """Find the requested folder in a full Kaggle download, ignoring case."""
    parts = [part for part in Path(subpath).parts if part not in {"/", "\\"}]
    direct = dataset_root.joinpath(*parts)
    if direct.is_dir():
        return direct

    target_name = parts[-1].casefold()
    matches = [
        path for path in dataset_root.rglob("*")
        if path.is_dir() and path.name.casefold() == target_name
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise RuntimeError(
            f"Found multiple folders named {parts[-1]!r} in {dataset_root}: "
            + ", ".join(str(path) for path in matches)
        )
    raise FileNotFoundError(
        f"Could not find {subpath!r} in {dataset_root}. "
        f"Top-level entries: {[path.name for path in dataset_root.iterdir()]}"
    )


def _cached_selected_folder(source: dict[str, str]) -> Path | None:
    """Reuse a prior KaggleHub download without contacting Kaggle again."""
    owner, slug = source["handle"].split("/", maxsplit=1)
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
        try:
            return _find_selected_folder(version_dir, source["subpath"])
        except FileNotFoundError:
            continue
    return None


def download_source(source: dict[str, str]) -> Path:
    """Download just the selected folder; fall back to the full dataset on folder 404."""
    cached_folder = _cached_selected_folder(source)
    if cached_folder is not None:
        print(f"Using cached {source['name']} folder: {cached_folder}")
        return cached_folder

    try:
        selected = Path(
            kagglehub.dataset_download(source["handle"], path=source["subpath"])
        )
        if selected.is_dir():
            return selected
    except Exception as error:
        if _http_status(error) != 404:
            raise
        print(
            f"Kaggle returned 404 for the selected folder in {source['handle']}; "
            "retrying with the full dataset."
        )

    dataset_root = Path(kagglehub.dataset_download(source["handle"]))
    if not dataset_root.is_dir():
        raise FileNotFoundError(f"KaggleHub returned a missing path: {dataset_root}")
    return _find_selected_folder(dataset_root, source["subpath"])


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="replace the extracted conjunctivitis image folder, preserving a backup",
    )
    args = parser.parse_args()

    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()) and not args.rebuild:
        raise FileExistsError(
            f"{OUTPUT_DIR} already contains images. Use `python conjunctivitis.py --rebuild` to refresh it."
        )

    # Collect and validate both source folders before changing the current output.
    selected_sources = [(source, download_source(source)) for source in SOURCES]
    staged_dir = DATA_DIR / f"conjunctivitis_build_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    staged_class_dir = staged_dir / "Conjunctivitis"
    staged_class_dir.mkdir(parents=True, exist_ok=True)

    counts = Counter()
    unreadable = 0
    duplicate_count = 0
    seen_hashes = set()

    for source, source_dir in selected_sources:
        source_images = 0
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

            source_images += 1
            if digest in seen_hashes:
                duplicate_count += 1
                continue
            seen_hashes.add(digest)
            destination = staged_class_dir / f"{source['name']}_{digest[:20]}{image_path.suffix.lower()}"
            shutil.copy2(image_path, destination)

        if source_images == 0:
            shutil.rmtree(staged_dir)
            raise ValueError(f"No readable image files found in selected folder: {source_dir}")
        counts[source["name"]] = source_images

    # Swap the completed extraction into place, retaining the prior copy if present.
    backup_dir = None
    if OUTPUT_DIR.exists():
        if OUTPUT_DIR.resolve().parent != DATA_DIR.resolve() or staged_dir.resolve().parent != DATA_DIR.resolve():
            shutil.rmtree(staged_dir)
            raise RuntimeError("Refusing to move image folders outside ml/data.")
        backup_dir = DATA_DIR / f"conjunctivitis_images_backup_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        shutil.move(str(OUTPUT_DIR), str(backup_dir))
    try:
        shutil.move(str(staged_dir), str(OUTPUT_DIR))
    except Exception:
        if backup_dir is not None and backup_dir.exists() and not OUTPUT_DIR.exists():
            shutil.move(str(backup_dir), str(OUTPUT_DIR))
        raise

    print(f"Output: {OUTPUT_CLASS_DIR}")
    print(f"{SOURCES[0]['name']} images: {counts[SOURCES[0]['name']]}")
    print(f"{SOURCES[1]['name']} images: {counts[SOURCES[1]['name']]}")
    unique_total = sum(1 for path in OUTPUT_CLASS_DIR.iterdir() if path.is_file())
    print(f"Total unique images: {unique_total}")
    print(f"Exact duplicate files skipped: {duplicate_count}")
    print(f"Unreadable images skipped: {unreadable}")


if __name__ == "__main__":
    main()
