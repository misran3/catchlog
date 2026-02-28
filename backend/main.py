# backend/main.py
"""FastAPI application for CatchLog."""

from contextlib import asynccontextmanager
from pathlib import Path
import io

from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image

from database import init_db
from inference import load_model
from agent import process_image, get_state, release_last
from models import Detection, AppState, ReleaseResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and model on startup."""
    init_db()
    load_model()
    yield


app = FastAPI(
    title="CatchLog API",
    description="On-device fishing compliance monitoring",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve audio files
audio_path = Path(__file__).parent / "audio"
if audio_path.exists():
    app.mount("/audio", StaticFiles(directory=audio_path), name="audio")


@app.post("/api/upload", response_model=Detection)
async def upload_image(file: UploadFile) -> Detection:
    """
    Upload an image for detection.

    Accepts: JPEG, PNG images
    Returns: Detection result with species, status, bbox, alert info
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Read and process image
    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents))
        image = image.convert("RGB")  # Ensure RGB format
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

    # Run detection pipeline
    detection = process_image(image, filename=file.filename)

    return detection


@app.get("/api/state", response_model=AppState)
async def get_app_state() -> AppState:
    """
    Get current application state.

    Returns: Last detection, frame, counts, alerts, compliance summary
    """
    return get_state()


@app.post("/api/release", response_model=ReleaseResponse)
async def release_catch() -> ReleaseResponse:
    """
    Mark the last unreleased bycatch/protected species as released.

    Returns: Release confirmation with updated compliance status
    """
    result = release_last()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="No unreleased bycatch or protected species to release"
        )

    return ReleaseResponse(**result)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
