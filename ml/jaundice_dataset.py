from pathlib import Path

from datasets import load_from_disk

# Load the dataset that was previously saved with ds.save_to_disk(...).
# This reads the local copy, so it does not need to download it from Hugging Face again.
dataset = load_from_disk("data/jaundice_dataset")

# Export each image as a separate JPEG, keeping train and test images in separate folders.
for split_name, split in dataset.items():
    # Create a folder for this split, such as data/jaundice_images/train.
    output_dir = Path("data/jaundice_images") / split_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Walk through every example in the split. Each example contains an image and a label.
    for index, example in enumerate(split):
        image = example["image"]
        label = example["label"]

        # Convert to RGB so grayscale or other image modes can be saved consistently as JPEG.
        image = image.convert("RGB")

        # Include the label in the filename to make the exported files easier to inspect.
        image_path = output_dir / f"{index}_label-{label}.jpg"
        image.save(image_path, format="JPEG")

    print(f"Exported {len(split)} images to {output_dir}")
