# ICheck frontend

This is a standalone HTML, CSS, and JavaScript frontend with no build tools or npm dependencies.

## Run

The FastAPI backend serves this folder directly, so the site and the API share one address. From `backend/`:

```sh
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`. The page posts the selected or captured image as multipart form data (field `file`) to `/api/v1/analyze`. API docs are at `http://127.0.0.1:8000/docs`.

### Optional: frontend-only server

`server.py` serves this folder on `http://127.0.0.1:5500` and forwards `/api/...` requests to the backend at `http://127.0.0.1:8000`. It is only needed if you want to run the frontend separately; the backend must still be running.

```sh
python frontend/server.py
```

## What the page uses from the API

- **Success:** `predicted_class`, `confidence`, `scores` (every class), `low_confidence`, `recommendation` (`title`, `description`, `next_steps`, `urgency`, `urgent_warning`) and `disclaimer`.
- **Errors:** `{"status": "error", "error_code": "...", "message": "..."}`. `message` is shown to the user as-is (e.g. a retake tip when a photo is too dark or blurry).

## Photos

- **Choose image** accepts JPG, PNG, WEBP and HEIC up to 15 MB.
- **Take photo on phones** (touch screens) uses `capture="environment"`, which opens the phone's own camera app. The site never gets live camera access; only the one photo the user confirms is returned to the page.
- **Take photo on laptops** opens a webcam preview dialog (`getUserMedia`). The browser asks for camera permission, the camera is switched off as soon as the dialog closes, and the captured frame goes through the same upload flow. Webcam access only works on `localhost` or HTTPS; elsewhere the button falls back to a file picker.
