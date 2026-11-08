"""Download the Kaggle cataract images and map their folders to project labels.

Run from the ml directory with: python cataract.py
The script maps Kaggle's normal class to Healthy and keeps Cataract as its own class.
"""

from collections import Counter
from hashlib import sha256
from pathlib import Path
import re
import shutil
import argparse

import kagglehub
from PIL import Image


DATASET_HANDLE = "nandanp6/cataract-image-dataset"
DATASET_SUBPATH = "processed_images"
OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "cataract_images"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def label_for_path(relative_path: Path) -> str | None:
    """Return a project label when a folder name or filename identifies the class."""
    normalized_parts = [
        re.sub(r"[^a-z0-9]+", "_", part.lower()) for part in relative_path.parts
    ]
    tokens = {
        token
        for part in relative_path.parts
        for token in re.split(r"[^a-z0-9]+", part.lower())
        if token
    }

    negative_cataract = any(
        phrase in part
        for part in normalized_parts
        for phrase in ("no_cataract", "non_cataract", "without_cataract", "cataract_free")
    ) or ("cataract" in tokens and bool({"no", "non", "without"} & tokens))
    if negative_cataract or {"normal", "healthy"} & tokens:
        return "Healthy"
    if any("cataract" in part for part in normalized_parts) or "cataract" in tokens:
        return "Cataract"
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="replace the extracted data/cataract_images folder",
    )
    args = parser.parse_args()

    # Download the dataset root first. Some Kaggle dataset versions return 404 for
    # a selected subfolder even when the dataset itself is available.
    dataset_dir = Path(kagglehub.dataset_download(DATASET_HANDLE))
    if not dataset_dir.exists():
        raise FileNotFoundError(f"KaggleHub returned a path that does not exist: {dataset_dir}")

    # Use the folder selected in the user's Kaggle URL. Resolve its actual casing
    # from the downloaded tree, since Kaggle file paths can be case-sensitive.
    source_dir = next(
        (
            path
            for path in dataset_dir.rglob("*")
            if path.is_dir() and path.name.casefold() == DATASET_SUBPATH.casefold()
        ),
        None,
    )
    if source_dir is None:
        top_level = [path.name for path in dataset_dir.iterdir()]
        raise FileNotFoundError(
            f"Could not find the {DATASET_SUBPATH!r} folder in {dataset_dir}. "
            f"Top-level entries: {top_level}"
        )

    # Avoid mixing a new download with files from an older extraction.
    if OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()):
        if not args.rebuild:
            raise FileExistsError(
                f"{OUTPUT_DIR} already contains extracted images. "
                "Run `python cataract.py --rebuild` to replace them."
            )
        expected_output = (Path(__file__).resolve().parent / "data" / "cataract_images").resolve()
        if OUTPUT_DIR.resolve() != expected_output:
            raise RuntimeError(f"Refusing to remove unexpected output path: {OUTPUT_DIR}")
        shutil.rmtree(OUTPUT_DIR)

    counts = Counter()
    unreadable = 0
    unlabelled = []
    copied_hashes = {}

    for source_path in source_dir.rglob("*"):
        if not source_path.is_file() or source_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        relative_path = source_path.relative_to(source_dir)
        label = label_for_path(relative_path)
        if label is None:
            unlabelled.append(str(relative_path))
            continue

        try:
            # Verify that the image can be decoded before copying it to the class folder.
            with Image.open(source_path) as image:
                image.verify()
            file_hash = sha256(source_path.read_bytes()).hexdigest()
        except Exception as error:
            unreadable += 1
            print(f"Skipping unreadable image {relative_path}: {error}")
            continue

        # Avoid creating duplicate copies when identical files occur more than once.
        if file_hash in copied_hashes:
            if copied_hashes[file_hash] != label:
                raise ValueError(
                    f"The same image file appears under both {copied_hashes[file_hash]} and {label}."
                )
            continue
        copied_hashes[file_hash] = label

        destination_dir = OUTPUT_DIR / label
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / f"{file_hash[:20]}{source_path.suffix.lower()}"
        shutil.copy2(source_path, destination)
        counts[label] += 1

    if not counts["Healthy"] or not counts["Cataract"]:
        examples = "\n".join(unlabelled[:20]) or "(no image files were found)"
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR)
        raise ValueError(
            "Could not identify images for both Normal/Healthy and Cataract in the downloaded folder. "
            f"Inspect these paths and update label_for_path():\n{examples}"
        )

    if unlabelled:
        examples = "\n".join(unlabelled[:20])
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR)
        raise ValueError(
            "Some image paths did not reveal a class label. Inspect these paths and update "
            f"label_for_path() before using the extraction:\n{examples}"
        )

    print(f"Downloaded source: {source_dir}")
    print(f"Mapped image folders: {OUTPUT_DIR}")
    print(f"Healthy (Kaggle Normal): {counts['Healthy']}")
    print(f"Cataract: {counts['Cataract']}")
    print(f"Unreadable images skipped: {unreadable}")
    print(f"Unrecognized image paths: {len(unlabelled)}")
    if unlabelled:
        print("Examples of unrecognized paths:")
        for path in unlabelled[:10]:
            print(f"  {path}")


if __name__ == "__main__":
    main()
