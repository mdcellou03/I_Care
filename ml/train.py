
from pathlib import Path
from fastai.vision.all import *
import torch

# Configuration
DATA_PATH = Path("data/processed")
MODEL_PATH = Path("models")
MODEL_PATH.mkdir(exist_ok=True)

torch.set_num_threads(4)

# Load images
dls = ImageDataLoaders.from_folder(
    DATA_PATH,
    train="train",
    valid="valid",
    item_tfms=Resize(224),
    bs=8,
    num_workers=0
)

print("Classes:", dls.vocab)
print("Training images:", len(dls.train_ds))
print("Validation images:", len(dls.valid_ds))

# Load pretrained ResNet18
learn = vision_learner(
    dls,
    resnet18,
    pretrained=True,
    metrics=accuracy
)

# Train classifier head with backbone frozen
learn.fit_one_cycle(1, 1e-3)

# Export model
learn.export(MODEL_PATH.resolve() / "eye_model.pkl")

print("Model saved to models/eye_model.pkl")
