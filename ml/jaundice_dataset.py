from datasets import load_dataset
from datasets import load_from_disk

ds = load_dataset("Bleachcarte/Jaundice_Dataset")

ds.save_to_disk("data/jaundice_dataset")