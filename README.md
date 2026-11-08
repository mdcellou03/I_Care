# ICheck

ICheck is an educational eye-health screening prototype. It combines a static HTML, CSS, and JavaScript frontend with a FastAPI service and a FastAI image-classification model. The app can also show nearby eye-care providers on a map.

> **Important:** This project is not a medical device. Its predictions are experimental, are not a diagnosis, and should not replace advice from an eye-care professional. Seek professional care for eye-health concerns.

## Project layout

```text
I_Care/
├── backend/       FastAPI app and API dependencies
├── frontend/      Static site, browser logic, and optional dev server
└── ml/            Model, recommendations, image checks, training and data tools
```

The trained model is expected at `ml/models/eye_model.pkl`. The backend loads it once when the API starts. The model was exported with Python 3.13; use Python 3.13 to run the backend and to load or retrain this model.

## Run the app locally

### 1. Create the backend environment

From the repository root, in PowerShell:

```powershell
py -3.13 -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirement.txt
```

If PowerShell blocks environment activation, you can run the environment's Python directly instead: `backend\.venv\Scripts\python.exe`.

### 2. Start the backend and frontend

From the repository root:

```powershell
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The FastAPI app serves the frontend and API from the same address. API documentation is at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), and the health endpoint is [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

The first startup can take a little while as FastAI and the model load. If startup reports a missing model, confirm `ml/models/eye_model.pkl` exists. If it reports a Python version mismatch, recreate the virtual environment with Python 3.13.

### Optional: run the frontend on its own port

The FastAPI backend must still be running. In a second terminal from the repository root:

```powershell
python frontend\server.py
```

Open [http://127.0.0.1:5500](http://127.0.0.1:5500). This small Python server serves the static frontend and forwards analysis requests to the backend on port 8000. It also forwards the nearby-provider search through its server-side proxy.

## Use the app

1. Choose or drop a clear eye image, or use **Take photo**.
2. Select **Analyze image** to send it to the API.
3. Review the experimental prediction, confidence, scores, and suggested next steps.
4. Select **Find optometrists near me** to request browser location and show nearby eye-care providers on the map. Select a listing for its address and Google Maps directions.

The image upload accepts JPG, PNG, WEBP, and HEIC/HEIF files up to 15 MB. The browser needs location permission for nearby search. Camera and location features require `localhost` or HTTPS. The map and provider lookup also need internet access. Provider results come from OpenStreetMap data and may be incomplete; Google Maps links provide another way to search.

## API

`POST /api/v1/analyze` accepts a multipart form upload with the field name `file`. On success, the response includes:

- `predicted_class`, `confidence`, and per-class `scores`
- `low_confidence`
- `recommendation` with a title, description, and next steps
- `disclaimer`

The backend validates file size and image quality, handles image orientation and HEIC decoding, and performs inference in memory. It does not save uploaded images.

## Train the model again

Training data is local and is not included in Git. Dataset scripts and source notes are in `ml/`; review [ml/DATASET_NOTES.md](ml/DATASET_NOTES.md) for dataset preparation and licensing context. The expected prepared layout is:

```text
ml/data/processed/
├── train/<class>/
├── valid/<class>/
└── test/<class>/
```

Install the ML dependencies in a Python 3.13 environment, then run preprocessing and training from `ml/`:

```powershell
cd ml
python -m pip install -r requirement.txt
python preprocess.py
python train.py
```

`train.py` exports `ml/models/eye_model.pkl`. The backend uses that path by default. Keep the training and backend Python version aligned with the exported model.

## Configuration

The backend reads optional settings from environment variables or `backend/.env`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `EYECHECK_ML_DIR` | Repository `ml/` folder | Location of the ML source and model directory |
| `EYECHECK_MODEL_PATH` | `ml/models/eye_model.pkl` | Model file to load |
| `EYECHECK_FRONTEND_DIR` | Repository `frontend/` folder | Static frontend directory served by FastAPI |
| `EYECHECK_ALLOWED_ORIGINS` | `http://localhost:5500` | Comma-separated browser origins allowed by CORS |

## Troubleshooting

- **Model or Python version error:** use Python 3.13 and verify the model file exists at `ml/models/eye_model.pkl`.
- **Frontend says it cannot reach the API:** start the backend. If using port 5500, keep both servers running.
- **Camera or location is unavailable:** use `localhost` or HTTPS and grant the browser permission.
- **Nearby providers do not appear:** verify internet access and try the Google Maps search link; OpenStreetMap listings are community maintained and can be incomplete.
- **ML install fails:** FastAI and PyTorch packages depend on Python and platform compatibility. Use the versions in `ml/requirement.txt` and follow the package's installation guidance for your platform if pip cannot resolve them.
