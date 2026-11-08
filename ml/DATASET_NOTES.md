# Dataset notes

## Combined experimental task

The planned class folders are `Healthy`, `Jaundice`, and `Cataract`.

- The existing Hugging Face dataset supplies `Healthy` and `Jaundice` visible-eye photos.
- The Kaggle cataract dataset is mapped by `cataract.py`: Kaggle `normal`/`healthy` becomes project `Healthy`; Kaggle `cataract` becomes `Cataract`.
- In the extracted `processed_images` folder, the script found 262 Healthy/Normal and 168 Cataract images. Combined with the saved jaundice source and after grouping 2 exact duplicates, the prepared set has 436 Healthy, 145 Jaundice, and 168 Cataract images (749 total).
- Seed-42 split counts: train 304 Healthy / 101 Jaundice / 116 Cataract; valid 66 / 22 / 26; test 66 / 22 / 26.
- These are visible-eye photographs, not retinal/fundus images. They come from different sources and may have different image styles; the classifier may learn source or capture differences. Inspect examples and class counts before training.
- The Kaggle license and provenance still need to be checked on its dataset page before redistribution: https://www.kaggle.com/datasets/nandanp6/cataract-image-dataset

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
python preprocess.py
```

`cataract.py` saves normalized Kaggle images locally under `data/cataract_images/Healthy` and `data/cataract_images/Cataract`. `preprocess.py` combines those with the saved Hugging Face images and writes the FastAI layout to `data/processed/{train,valid,test}/{Healthy,Jaundice,Cataract}`. The earlier two-class output is preserved locally as `data/processed_two_class_backup`. If you later need to regenerate the current output, use `python preprocess.py --rebuild`.

The preprocessing uses seed 42 and groups exact duplicate decoded pixels before splitting. Patient IDs are not available, and near-duplicates may remain. It makes a new 70/15/15 split across all examples, so any source-provided train/test separation is not preserved. Treat model results as experimental, not as clinical validation or diagnosis.

All local data under `ml/data/` is excluded from Git by `ml/.gitignore`. Do not redistribute either dataset until their license terms are reviewed.
