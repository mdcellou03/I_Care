# Dataset notes

## Combined experimental task

The planned class folders are `Healthy`, `Jaundice`, `Cataract`, `Conjunctivitis`, and `Uveitis`.

- The existing Hugging Face dataset supplies `Healthy` and `Jaundice` visible-eye photos.
- The Kaggle cataract dataset is mapped by `cataract.py`: Kaggle `normal`/`healthy` becomes project `Healthy`; Kaggle `cataract` becomes `Cataract`.
- The two conjunctivitis sources are mapped by `conjunctivitis.py` into `data/conjunctivitis_images/Conjunctivitis`: Kaggle `Dataset/infected_eye` and the second dataset's `Conjunctivitis` class folder.
- The Orvile Kaggle `Uveitis` folder is mapped by `uveitis.py` into `data/uveitis_images/Uveitis`.
- Before adding conjunctivitis, the prepared set had 436 Healthy, 145 Jaundice, and 168 Cataract images (749 total), with 2 exact duplicates grouped. Rebuild to get the new counts; `preprocess.py` prints counts per class and split.
- The conjunctivitis extraction found 177 readable images in the first source and 357 in the second; one byte-identical file was skipped. Preprocessing then grouped one additional exact-pixel duplicate, leaving 532 Conjunctivitis images.
- Before adding Uveitis, the four-class output had 1,281 images.
- Uveitis extraction found 223 readable images with no exact duplicate files. The current five-class output has 1,504 images: Healthy 436, Jaundice 145, Cataract 168, Conjunctivitis 532, and Uveitis 223.
- Current seed-42 split counts in that class order: train 304 / 101 / 116 / 372 / 155; valid 66 / 22 / 26 / 80 / 34; test 66 / 22 / 26 / 80 / 34.
- These are visible-eye photographs, not retinal/fundus images. They come from different sources and may have different image styles; the classifier may learn source or capture differences. Inspect examples and class counts before training.
- Check the license and provenance for each Kaggle source on its dataset page before redistribution: [cataract](https://www.kaggle.com/datasets/nandanp6/cataract-image-dataset), [conjunctivitis source 1](https://www.kaggle.com/datasets/alisofiya/conjunctivitis), and [conjunctivitis source 2](https://www.kaggle.com/datasets/orvile/eye-diseases-classification).

## Existing jaundice source

- Source: `Bleachcarte/Jaundice_Dataset` on Hugging Face.
- License shown on its dataset card: CC BY-NC 4.0 (attribution required; non-commercial use only).
- Source description: web-scraped images, not clinically validated; image lighting, camera quality, and zoom vary.
- Fields: `image` and `label`; no patient identifiers are supplied.
- Labels/counts in the downloaded copy: Healthy 176 total (141 original train, 35 original test); Jaundice 145 total (115 original train, 30 original test).

## Preparation

Install requirements, download/map the Kaggle classes, then rebuild the combined splits from `I_Care/ml`:

```bash
python -m pip install -r requirement.txt
python cataract.py
python conjunctivitis.py
python uveitis.py
python preprocess.py --rebuild
```

`cataract.py` saves normalized Kaggle images under `data/cataract_images/Healthy` and `data/cataract_images/Cataract`. `conjunctivitis.py` saves images from both specified Kaggle folders under `data/conjunctivitis_images/Conjunctivitis`. `uveitis.py` saves the selected Uveitis images under `data/uveitis_images/Uveitis`. `preprocess.py` combines these with the saved Hugging Face images and writes the FastAI layout to `data/processed/{train,valid,test}/{Healthy,Jaundice,Cataract,Conjunctivitis,Uveitis}`. It keeps the previous output as a local backup when rebuilding.

The preprocessing uses seed 42 and groups exact duplicate decoded pixels before splitting. Patient IDs are not available, and near-duplicates may remain. It makes a new 70/15/15 split across all examples, so any source-provided train/test separation is not preserved. Treat model results as experimental, not as clinical validation or diagnosis.

All local data under `ml/data/` is excluded from Git by the repository `.gitignore`. Do not redistribute any of these datasets until their license terms are reviewed.
