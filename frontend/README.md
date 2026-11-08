# ICheck frontend

This is a standalone HTML, CSS, and JavaScript frontend. The repository's `ml/requirement.txt` lists Python machine-learning dependencies, not frontend packages, so this interface uses no frontend build tools or npm dependencies.

## Run

Start the FastAPI backend on `127.0.0.1:8000`, then start the frontend proxy from the repository root:

```sh
python frontend/server.py
```

Open `http://127.0.0.1:5500`. The page posts the selected image as multipart form data to `/api/v1/analyze`; the included local server forwards API requests to the backend without requiring backend or CORS changes. The backend can be hosted elsewhere by changing `BACKEND_URL` in `server.py`.

The current backend response provides the predicted class, confidence, class scores, and disclaimer. Recommendation details are displayed if the API includes a `recommendation` object.
