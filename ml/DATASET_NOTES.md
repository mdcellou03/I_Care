# Dataset notes

- Source: `Bleachcarte/Jaundice_Dataset` on Hugging Face.
- License shown on the dataset card: CC BY-NC 4.0 (attribution required; non-commercial use only).
- Image type: web-scraped photographs of visible human eyes; these are not retinal/fundus images.
- Source description: educational/prototyping/research use; images are not clinically validated and have varied lighting, camera quality, and zoom.
- Features: `image`, `label`; no patient identifiers are supplied.
- Labels: `Healthy` and `Jaundice`.
- Original counts: 321 total; original train 256 (Healthy 141, Jaundice 115); original test 65 (Healthy 35, Jaundice 30).
- Current processed counts after exact-pixel deduplication and seeded split: train 223 (Healthy 122, Jaundice 101), valid 49 (Healthy 27, Jaundice 22), test 49 (Healthy 27, Jaundice 22).
- Split method: per-class, fixed random seed 42; exact pixel duplicates are grouped before splitting. There were no unreadable images or exact duplicate copies in this copy of the dataset.
- Limitations: patient-level separation cannot be guaranteed because patient IDs are absent; near-duplicates may remain. The newly generated test split is an experimental holdout, not clinical validation.
- The local source and processed images are excluded from Git by `ml/.gitignore`. Do not publish or use the dataset commercially; check the source card and license obligations before redistribution.

From the `I_Care/ml` directory, install requirements and reproduce the output:

```bash
python -m pip install -r requirement.txt
python preprocess.py
```

The script loads `data/jaundice_dataset` if already downloaded, otherwise fetches and saves the source dataset. It writes the FastAI-compatible structure under `data/processed/`.
