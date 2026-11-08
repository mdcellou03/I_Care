"""Entry point for the EyeCheck API. Creates the app, loads the model and registers routes.

Run from backend/:  uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
from fastapi.staticfiles import staticFiles
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS, FRONTEND_DIR
from app.errors import register_error_handlers
from app.routes import analyze
from app.services import predictor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when the server starts (code before `yield`) and once when it stops."""
    # Load the model at startup: a missing or broken model fails immediately,
    # and the first user doesn't wait for it to load.
    predictor.get_learner()
    yield


app = FastAPI(title="EyeCheck API", version="0.1.0", lifespan=lifespan)

# Only needed when the frontend runs on another origin (e.g. frontend/server.py on :5500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
register_error_handlers(app)
app.include_router(analyze.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Simple check that the server is up."""
    return {"status": "ok"}

# Serve the frontend last: a mount at "/" catches every path, so the API routes above
# have to be registered first. html=True makes "/" return index.html.
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")