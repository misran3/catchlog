# CatchLog Backend + UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a working FastAPI backend and Next.js dashboard for the CatchLog fishing compliance POC.

**Architecture:** Backend-first approach. FastAPI serves 3 endpoints (upload, state, release). Next.js dashboard polls state and displays detections. Mock inference until real model is ready.

**Tech Stack:** Python 3.11+ (uv), FastAPI, SQLite, Pillow | Next.js 14, TypeScript, Tailwind CSS (bun)

---

## Phase 1: Backend Setup

### Task 1: Initialize Backend Project

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.python-version`

**Step 1: Create backend directory and pyproject.toml**

```bash
mkdir -p backend
```

```toml
# backend/pyproject.toml
[project]
name = "catchlog-backend"
version = "0.1.0"
description = "CatchLog fishing compliance API"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "python-multipart>=0.0.6",
    "pillow>=10.2.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "httpx>=0.26.0",
]
```

**Step 2: Create .python-version**

```
# backend/.python-version
3.11
```

**Step 3: Initialize uv and install dependencies**

```bash
cd backend && uv sync
```

Expected: Dependencies installed, `.venv` created.

**Step 4: Verify installation**

```bash
cd backend && uv run python -c "import fastapi; print(fastapi.__version__)"
```

Expected: Prints FastAPI version (e.g., `0.109.0`)

**Step 5: Commit**

```bash
git add backend/pyproject.toml backend/.python-version backend/uv.lock
git commit -m "feat(backend): initialize project with uv and FastAPI"
```

---

### Task 2: Create Pydantic Models

**Files:**
- Create: `backend/models.py`

**Step 1: Write models.py**

```python
# backend/models.py
"""Pydantic models for API request/response validation."""

from enum import IntEnum
from pydantic import BaseModel


class SpeciesStatus(IntEnum):
    """Species regulatory status."""
    LEGAL = 0
    BYCATCH = 1
    PROTECTED = 2
    UNKNOWN = 3


class AlertLevel(str):
    """Alert severity levels."""
    NONE = "none"
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Detection(BaseModel):
    """Single detection result from inference."""
    detection_id: int
    timestamp: str
    species: str
    status: str  # legal | bycatch | protected | unknown
    confidence: float
    bbox: list[int]  # [x1, y1, x2, y2]
    alert_level: str
    audio_url: str | None = None


class Alert(BaseModel):
    """Alert entry for the feed."""
    timestamp: str
    message: str
    level: str


class Compliance(BaseModel):
    """Compliance summary statistics."""
    total: int
    legal: int
    bycatch: int
    protected: int
    released: int
    status: str  # COMPLIANT | ACTION_REQUIRED


class AppState(BaseModel):
    """Full application state for dashboard."""
    last_detection: Detection | None = None
    frame_base64: str | None = None
    counts: dict[str, int]
    alerts: list[Alert]
    compliance: Compliance


class ReleaseResponse(BaseModel):
    """Response from release endpoint."""
    released_id: int
    species: str
    compliance_status: str
```

**Step 2: Verify models load**

```bash
cd backend && uv run python -c "from models import Detection, AppState; print('Models OK')"
```

Expected: `Models OK`

**Step 3: Commit**

```bash
git add backend/models.py
git commit -m "feat(backend): add Pydantic models for API contracts"
```

---

### Task 3: Implement Database Layer

**Files:**
- Create: `backend/database.py`

**Step 1: Write database.py**

```python
# backend/database.py
"""SQLite database operations for catch logging."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "catch_log.db"

# Species seed data: (id, name, status)
# Status: 0=legal, 1=bycatch, 2=protected, 3=unknown
SPECIES_DATA = [
    (1, "Albacore Tuna", 0),
    (2, "Bigeye Tuna", 0),
    (3, "Mahi-Mahi", 0),
    (4, "Blue Shark", 1),
    (5, "Sea Turtle", 2),
    (6, "Unknown", 3),
]


def init_db() -> None:
    """Initialize database schema and seed data."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS species (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                status INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL,
                species_id INTEGER NOT NULL,
                released INTEGER DEFAULT 0,
                FOREIGN KEY (species_id) REFERENCES species(id)
            );
        """)

        # Seed species if empty
        cursor = conn.execute("SELECT COUNT(*) FROM species")
        if cursor.fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO species (id, name, status) VALUES (?, ?, ?)",
                SPECIES_DATA
            )
        conn.commit()


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_species_by_id(species_id: int) -> dict | None:
    """Get species info by ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, name, status FROM species WHERE id = ?",
            (species_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_species_by_name(name: str) -> dict | None:
    """Get species info by name."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, name, status FROM species WHERE name = ?",
            (name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_species() -> list[dict]:
    """Get all species."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT id, name, status FROM species")
        return [dict(row) for row in cursor.fetchall()]


def log_detection(ts: int, species_id: int) -> int:
    """Log a detection, return the new detection ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO detections (ts, species_id) VALUES (?, ?)",
            (ts, species_id)
        )
        conn.commit()
        return cursor.lastrowid


def mark_released(detection_id: int) -> bool:
    """Mark a detection as released. Returns True if updated."""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE detections SET released = 1 WHERE id = ? AND released = 0",
            (detection_id,)
        )
        conn.commit()
        return cursor.rowcount > 0


def get_last_unreleased_alert() -> dict | None:
    """Get the most recent unreleased bycatch/protected detection."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT d.id, d.ts, s.name, s.status
            FROM detections d
            JOIN species s ON d.species_id = s.id
            WHERE d.released = 0 AND s.status IN (1, 2)
            ORDER BY d.id DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        return dict(row) if row else None


def get_detection_counts() -> dict[str, int]:
    """Get count of detections per species."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT s.name, COUNT(*) as count
            FROM detections d
            JOIN species s ON d.species_id = s.id
            GROUP BY s.name
        """)
        return {row["name"]: row["count"] for row in cursor.fetchall()}


def get_compliance_stats() -> dict:
    """Get compliance statistics."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN s.status = 0 THEN 1 ELSE 0 END) as legal,
                SUM(CASE WHEN s.status = 1 THEN 1 ELSE 0 END) as bycatch,
                SUM(CASE WHEN s.status = 2 THEN 1 ELSE 0 END) as protected,
                SUM(CASE WHEN d.released = 1 THEN 1 ELSE 0 END) as released
            FROM detections d
            JOIN species s ON d.species_id = s.id
        """)
        row = cursor.fetchone()
        stats = dict(row)

        # Determine compliance status
        unreleased_issues = (stats["bycatch"] + stats["protected"]) - stats["released"]
        stats["status"] = "COMPLIANT" if unreleased_issues <= 0 else "ACTION_REQUIRED"

        return stats


def reset_db() -> None:
    """Reset database (for testing)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM detections")
        conn.commit()
```

**Step 2: Test database initialization**

```bash
cd backend && uv run python -c "
from database import init_db, get_all_species, log_detection, get_detection_counts
import time

init_db()
species = get_all_species()
print(f'Species loaded: {len(species)}')

# Test logging
det_id = log_detection(int(time.time()), 1)
print(f'Logged detection ID: {det_id}')

counts = get_detection_counts()
print(f'Counts: {counts}')
"
```

Expected:
```
Species loaded: 6
Logged detection ID: 1
Counts: {'Albacore Tuna': 1}
```

**Step 3: Clean up test DB and commit**

```bash
rm -f backend/catch_log.db
git add backend/database.py
git commit -m "feat(backend): add SQLite database layer with CRUD operations"
```

---

### Task 4: Implement Mock Inference

**Files:**
- Create: `backend/inference.py`

**Step 1: Write inference.py**

```python
# backend/inference.py
"""Mock inference module - swap for real model later."""

import random
from dataclasses import dataclass
from PIL import Image


@dataclass
class InferenceResult:
    """Result from running inference on an image."""
    species: str
    confidence: float
    bbox: list[int]  # [x1, y1, x2, y2]


# Weighted species distribution for realistic demo
# Format: (species_name, weight)
SPECIES_WEIGHTS = [
    ("Albacore Tuna", 30),  # Legal - common
    ("Bigeye Tuna", 25),    # Legal - common
    ("Mahi-Mahi", 15),      # Legal - less common
    ("Blue Shark", 20),     # Bycatch
    ("Sea Turtle", 8),      # Protected - rare
    ("Unknown", 2),         # Unknown - very rare
]


def _weighted_random_species() -> str:
    """Pick a species based on weighted distribution."""
    species_list = [s for s, _ in SPECIES_WEIGHTS]
    weights = [w for _, w in SPECIES_WEIGHTS]
    return random.choices(species_list, weights=weights, k=1)[0]


def _random_bbox(width: int, height: int) -> list[int]:
    """Generate a random bounding box within image bounds."""
    # Box should be 20-40% of image size
    box_w = random.randint(int(width * 0.2), int(width * 0.4))
    box_h = random.randint(int(height * 0.2), int(height * 0.4))

    # Random position (ensure box fits)
    x1 = random.randint(0, width - box_w)
    y1 = random.randint(0, height - box_h)
    x2 = x1 + box_w
    y2 = y1 + box_h

    return [x1, y1, x2, y2]


def run_inference(image: Image.Image) -> InferenceResult:
    """
    Run mock inference on an image.

    In production, this would:
    1. Preprocess image for PaliGemma
    2. Run model forward pass
    3. Parse detection output

    For now, returns random realistic results.
    """
    width, height = image.size

    return InferenceResult(
        species=_weighted_random_species(),
        confidence=round(random.uniform(0.75, 0.98), 2),
        bbox=_random_bbox(width, height),
    )


# === Interface for swapping in real model ===

_model = None


def load_model(model_path: str | None = None) -> None:
    """
    Load the inference model.

    For mock: does nothing.
    For real model: loads PaliGemma + LoRA weights.
    """
    global _model
    # TODO: Load real model when ready
    # from transformers import AutoProcessor, PaliGemmaForConditionalGeneration
    # _model = PaliGemmaForConditionalGeneration.from_pretrained(...)
    _model = "mock"


def is_model_loaded() -> bool:
    """Check if model is loaded."""
    return _model is not None
```

**Step 2: Test inference**

```bash
cd backend && uv run python -c "
from inference import run_inference, load_model
from PIL import Image

load_model()

# Create test image
img = Image.new('RGB', (640, 480), color='blue')
result = run_inference(img)

print(f'Species: {result.species}')
print(f'Confidence: {result.confidence}')
print(f'Bbox: {result.bbox}')
"
```

Expected: Random species, confidence 0.75-0.98, bbox within image bounds.

**Step 3: Commit**

```bash
git add backend/inference.py
git commit -m "feat(backend): add mock inference module with weighted species distribution"
```

---

### Task 5: Implement Agent Logic

**Files:**
- Create: `backend/agent.py`

**Step 1: Write agent.py**

```python
# backend/agent.py
"""CatchLog Agent - decision engine for detection processing."""

import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from PIL import Image
import io
import base64

from models import Detection, Alert, Compliance, AppState, AlertLevel
from database import (
    get_species_by_name,
    log_detection,
    get_detection_counts,
    get_compliance_stats,
    mark_released,
    get_last_unreleased_alert,
)
from inference import run_inference, InferenceResult


# Alert level mapping by species status
STATUS_TO_ALERT = {
    0: AlertLevel.NONE,      # Legal
    1: AlertLevel.WARNING,   # Bycatch
    2: AlertLevel.CRITICAL,  # Protected
    3: AlertLevel.INFO,      # Unknown
}

STATUS_NAMES = {
    0: "legal",
    1: "bycatch",
    2: "protected",
    3: "unknown",
}

AUDIO_URLS = {
    AlertLevel.WARNING: "/audio/alert_warning.mp3",
    AlertLevel.CRITICAL: "/audio/alert_critical.mp3",
    AlertLevel.INFO: "/audio/alert_info.mp3",
}


@dataclass
class AgentState:
    """In-memory state for the agent."""
    last_detection: Detection | None = None
    frame_base64: str | None = None
    alerts: list[Alert] = field(default_factory=list)


# Global agent state
_state = AgentState()


def process_image(image: Image.Image) -> Detection:
    """
    Process an uploaded image through the full pipeline.

    1. Run inference
    2. Look up species regulation
    3. Log to database
    4. Generate alert if needed
    5. Update in-memory state
    """
    # Run inference
    result: InferenceResult = run_inference(image)

    # Get species info from DB
    species_info = get_species_by_name(result.species)
    if not species_info:
        # Fallback to Unknown
        species_info = get_species_by_name("Unknown")

    # Log to database
    ts = int(time.time())
    detection_id = log_detection(ts, species_info["id"])

    # Determine alert level
    status_code = species_info["status"]
    alert_level = STATUS_TO_ALERT.get(status_code, AlertLevel.INFO)
    status_name = STATUS_NAMES.get(status_code, "unknown")

    # Get audio URL if alert needed
    audio_url = AUDIO_URLS.get(alert_level) if alert_level != AlertLevel.NONE else None

    # Create detection object
    timestamp = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    detection = Detection(
        detection_id=detection_id,
        timestamp=timestamp,
        species=result.species,
        status=status_name,
        confidence=result.confidence,
        bbox=result.bbox,
        alert_level=alert_level,
        audio_url=audio_url,
    )

    # Draw bbox on image and encode
    frame_with_bbox = _draw_bbox(image.copy(), result.bbox, status_code)
    _state.frame_base64 = _image_to_base64(frame_with_bbox)

    # Update state
    _state.last_detection = detection

    # Add to alerts if not legal
    if alert_level != AlertLevel.NONE:
        alert_msg = _format_alert_message(result.species, status_name)
        _state.alerts.append(Alert(
            timestamp=timestamp,
            message=alert_msg,
            level=alert_level,
        ))
        # Keep last 50 alerts
        _state.alerts = _state.alerts[-50:]

    return detection


def _draw_bbox(image: Image.Image, bbox: list[int], status: int) -> Image.Image:
    """Draw bounding box on image with color based on status."""
    from PIL import ImageDraw

    colors = {
        0: "#22c55e",  # Green - legal
        1: "#eab308",  # Yellow - bycatch
        2: "#ef4444",  # Red - protected
        3: "#6b7280",  # Gray - unknown
    }
    color = colors.get(status, "#6b7280")

    draw = ImageDraw.Draw(image)
    x1, y1, x2, y2 = bbox
    draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

    return image


def _image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 data URL."""
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}"


def _format_alert_message(species: str, status: str) -> str:
    """Format alert message based on status."""
    if status == "bycatch":
        return f"BYCATCH: {species} — Release required"
    elif status == "protected":
        return f"PROTECTED: {species} — Immediate release required"
    elif status == "unknown":
        return f"UNKNOWN: {species} — Flagged for review"
    return f"{species} detected"


def get_state() -> AppState:
    """Get current application state for dashboard."""
    counts = get_detection_counts()
    stats = get_compliance_stats()

    compliance = Compliance(
        total=stats["total"],
        legal=stats["legal"],
        bycatch=stats["bycatch"],
        protected=stats["protected"],
        released=stats["released"],
        status=stats["status"],
    )

    return AppState(
        last_detection=_state.last_detection,
        frame_base64=_state.frame_base64,
        counts=counts,
        alerts=_state.alerts,
        compliance=compliance,
    )


def release_last() -> dict | None:
    """
    Mark the last unreleased bycatch/protected as released.

    Returns release info or None if nothing to release.
    """
    unreleased = get_last_unreleased_alert()
    if not unreleased:
        return None

    mark_released(unreleased["id"])
    stats = get_compliance_stats()

    return {
        "released_id": unreleased["id"],
        "species": unreleased["name"],
        "compliance_status": stats["status"],
    }


def reset_state() -> None:
    """Reset agent state (for testing)."""
    global _state
    _state = AgentState()
```

**Step 2: Test agent**

```bash
cd backend && uv run python -c "
from agent import process_image, get_state, reset_state
from database import init_db, reset_db
from inference import load_model
from PIL import Image

init_db()
reset_db()
reset_state()
load_model()

# Process test image
img = Image.new('RGB', (640, 480), color='blue')
detection = process_image(img)

print(f'Detection: {detection.species} ({detection.status})')
print(f'Alert level: {detection.alert_level}')

state = get_state()
print(f'Total detections: {state.compliance.total}')
print(f'Has frame: {state.frame_base64 is not None}')
"
```

Expected: Detection logged, state updated, frame encoded.

**Step 3: Clean up and commit**

```bash
rm -f backend/catch_log.db
git add backend/agent.py
git commit -m "feat(backend): add CatchLogAgent with detection processing pipeline"
```

---

### Task 6: Implement FastAPI Routes

**Files:**
- Create: `backend/main.py`
- Create: `backend/audio/` directory with placeholder

**Step 1: Create audio directory**

```bash
mkdir -p backend/audio
touch backend/audio/.gitkeep
```

**Step 2: Write main.py**

```python
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
    detection = process_image(image)

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
```

**Step 3: Test the API server**

```bash
cd backend && uv run uvicorn main:app --reload --port 8000 &
sleep 3

# Test health endpoint
curl http://localhost:8000/health

# Test state endpoint (should be empty)
curl http://localhost:8000/api/state

# Stop server
pkill -f "uvicorn main:app"
```

Expected: Health returns `{"status":"ok"}`, state returns empty compliance.

**Step 4: Clean up and commit**

```bash
rm -f backend/catch_log.db
git add backend/main.py backend/audio/.gitkeep
git commit -m "feat(backend): add FastAPI routes for upload, state, and release"
```

---

### Task 7: Backend Integration Test

**Files:**
- Create: `backend/tests/test_api.py`

**Step 1: Create test directory and file**

```bash
mkdir -p backend/tests
touch backend/tests/__init__.py
```

```python
# backend/tests/test_api.py
"""Integration tests for CatchLog API."""

import pytest
from fastapi.testclient import TestClient
from PIL import Image
import io

from main import app
from database import reset_db
from agent import reset_state


@pytest.fixture(autouse=True)
def clean_state():
    """Reset state before each test."""
    reset_db()
    reset_state()
    yield


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def test_image() -> bytes:
    """Create a test image."""
    img = Image.new("RGB", (640, 480), color="blue")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_health(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_initial_state(client):
    """Test state is empty initially."""
    response = client.get("/api/state")
    assert response.status_code == 200

    data = response.json()
    assert data["last_detection"] is None
    assert data["compliance"]["total"] == 0


def test_upload_image(client, test_image):
    """Test uploading an image creates a detection."""
    response = client.post(
        "/api/upload",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )
    assert response.status_code == 200

    data = response.json()
    assert "detection_id" in data
    assert "species" in data
    assert "status" in data
    assert "bbox" in data
    assert len(data["bbox"]) == 4


def test_state_after_upload(client, test_image):
    """Test state updates after upload."""
    # Upload image
    client.post(
        "/api/upload",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )

    # Check state
    response = client.get("/api/state")
    data = response.json()

    assert data["last_detection"] is not None
    assert data["frame_base64"] is not None
    assert data["compliance"]["total"] == 1


def test_release_nothing(client):
    """Test release with no unreleased items."""
    response = client.post("/api/release")
    assert response.status_code == 404


def test_invalid_file(client):
    """Test uploading non-image file."""
    response = client.post(
        "/api/upload",
        files={"file": ("test.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400
```

**Step 2: Run tests**

```bash
cd backend && uv run pytest tests/ -v
```

Expected: All tests pass.

**Step 3: Commit**

```bash
rm -f backend/catch_log.db
git add backend/tests/
git commit -m "test(backend): add API integration tests"
```

---

## Phase 2: Frontend Setup

### Task 8: Initialize Frontend Project

**Files:**
- Create: `frontend/` directory with Next.js app

**Step 1: Create Next.js app with bun**

```bash
cd /Users/misran/Documents/misu/instalily-ai-hackathon/catchlog
bunx create-next-app@14 frontend --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*" --use-bun
```

Accept defaults when prompted.

**Step 2: Verify installation**

```bash
cd frontend && bun run build
```

Expected: Build succeeds.

**Step 3: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): initialize Next.js 14 with Tailwind"
```

---

### Task 9: Create API Client

**Files:**
- Create: `frontend/lib/api.ts`
- Create: `frontend/lib/types.ts`

**Step 1: Create lib directory**

```bash
mkdir -p frontend/lib
```

**Step 2: Write types.ts**

```typescript
// frontend/lib/types.ts

export interface Detection {
  detection_id: number;
  timestamp: string;
  species: string;
  status: "legal" | "bycatch" | "protected" | "unknown";
  confidence: number;
  bbox: [number, number, number, number];
  alert_level: "none" | "info" | "warning" | "critical";
  audio_url: string | null;
}

export interface Alert {
  timestamp: string;
  message: string;
  level: "info" | "warning" | "critical";
}

export interface Compliance {
  total: number;
  legal: number;
  bycatch: number;
  protected: number;
  released: number;
  status: "COMPLIANT" | "ACTION_REQUIRED";
}

export interface AppState {
  last_detection: Detection | null;
  frame_base64: string | null;
  counts: Record<string, number>;
  alerts: Alert[];
  compliance: Compliance;
}

export interface ReleaseResponse {
  released_id: number;
  species: string;
  compliance_status: string;
}
```

**Step 3: Write api.ts**

```typescript
// frontend/lib/api.ts

import type { Detection, AppState, ReleaseResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function uploadImage(file: File): Promise<Detection> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }

  return response.json();
}

export async function getState(): Promise<AppState> {
  const response = await fetch(`${API_BASE}/api/state`);

  if (!response.ok) {
    throw new Error(`Failed to get state: ${response.statusText}`);
  }

  return response.json();
}

export async function releaseLastCatch(): Promise<ReleaseResponse> {
  const response = await fetch(`${API_BASE}/api/release`, {
    method: "POST",
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("No unreleased catch to release");
    }
    throw new Error(`Release failed: ${response.statusText}`);
  }

  return response.json();
}

export function getAudioUrl(path: string): string {
  return `${API_BASE}${path}`;
}
```

**Step 4: Commit**

```bash
git add frontend/lib/
git commit -m "feat(frontend): add API client and TypeScript types"
```

---

### Task 10: Create ImageUpload Component

**Files:**
- Create: `frontend/components/ImageUpload.tsx`

**Step 1: Create components directory**

```bash
mkdir -p frontend/components
```

**Step 2: Write ImageUpload.tsx**

```typescript
// frontend/components/ImageUpload.tsx
"use client";

import { useCallback, useState } from "react";
import { uploadImage } from "@/lib/api";
import type { Detection } from "@/lib/types";

interface ImageUploadProps {
  onDetection: (detection: Detection) => void;
}

export function ImageUpload({ onDetection }: ImageUploadProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.type.startsWith("image/")) {
        alert("Please upload an image file");
        return;
      }

      setIsUploading(true);
      try {
        const detection = await uploadImage(file);
        onDetection(detection);
      } catch (error) {
        console.error("Upload failed:", error);
        alert("Failed to upload image");
      } finally {
        setIsUploading(false);
      }
    },
    [onDetection]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);

      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div
      className={`
        border-2 border-dashed rounded-lg p-6 text-center cursor-pointer
        transition-colors duration-200
        ${dragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"}
        ${isUploading ? "opacity-50 pointer-events-none" : ""}
      `}
      onDragOver={(e) => {
        e.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={handleDrop}
      onClick={() => document.getElementById("file-input")?.click()}
    >
      <input
        id="file-input"
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleChange}
        disabled={isUploading}
      />

      {isUploading ? (
        <div className="flex items-center justify-center gap-2">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-600">Processing...</span>
        </div>
      ) : (
        <div>
          <div className="text-3xl mb-2">📷</div>
          <p className="text-gray-600">
            Drop image here or <span className="text-blue-500">browse</span>
          </p>
        </div>
      )}
    </div>
  );
}
```

**Step 3: Commit**

```bash
git add frontend/components/ImageUpload.tsx
git commit -m "feat(frontend): add ImageUpload component with drag-drop"
```

---

### Task 11: Create VideoFeed Component

**Files:**
- Create: `frontend/components/VideoFeed.tsx`

**Step 1: Write VideoFeed.tsx**

```typescript
// frontend/components/VideoFeed.tsx
"use client";

interface VideoFeedProps {
  frameBase64: string | null;
  species?: string;
  status?: string;
}

export function VideoFeed({ frameBase64, species, status }: VideoFeedProps) {
  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden">
      <div className="aspect-video relative flex items-center justify-center">
        {frameBase64 ? (
          <>
            <img
              src={frameBase64}
              alt="Detection frame"
              className="w-full h-full object-contain"
            />
            {species && (
              <div
                className={`
                  absolute bottom-4 left-4 px-3 py-1 rounded-full text-sm font-medium
                  ${status === "legal" ? "bg-green-500 text-white" : ""}
                  ${status === "bycatch" ? "bg-yellow-500 text-black" : ""}
                  ${status === "protected" ? "bg-red-500 text-white" : ""}
                  ${status === "unknown" ? "bg-gray-500 text-white" : ""}
                `}
              >
                {species}
              </div>
            )}
          </>
        ) : (
          <div className="text-gray-500 text-center">
            <div className="text-5xl mb-2">🐟</div>
            <p>No image uploaded yet</p>
          </div>
        )}
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/components/VideoFeed.tsx
git commit -m "feat(frontend): add VideoFeed component for displaying detections"
```

---

### Task 12: Create CatchCounter Component

**Files:**
- Create: `frontend/components/CatchCounter.tsx`

**Step 1: Write CatchCounter.tsx**

```typescript
// frontend/components/CatchCounter.tsx
"use client";

interface CatchCounterProps {
  counts: Record<string, number>;
}

// Map species to their status for styling
const SPECIES_STATUS: Record<string, "legal" | "bycatch" | "protected" | "unknown"> = {
  "Albacore Tuna": "legal",
  "Bigeye Tuna": "legal",
  "Mahi-Mahi": "legal",
  "Blue Shark": "bycatch",
  "Sea Turtle": "protected",
  "Unknown": "unknown",
};

export function CatchCounter({ counts }: CatchCounterProps) {
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-semibold mb-3 text-gray-800">Catch Counter</h2>

      {entries.length === 0 ? (
        <p className="text-gray-500 text-sm">No catches recorded</p>
      ) : (
        <div className="space-y-2">
          {entries.map(([species, count]) => {
            const status = SPECIES_STATUS[species] || "unknown";
            return (
              <div
                key={species}
                className="flex items-center justify-between py-1"
              >
                <div className="flex items-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full
                      ${status === "legal" ? "bg-green-500" : ""}
                      ${status === "bycatch" ? "bg-yellow-500" : ""}
                      ${status === "protected" ? "bg-red-500" : ""}
                      ${status === "unknown" ? "bg-gray-400" : ""}
                    `}
                  />
                  <span className="text-sm text-gray-700">{species}</span>
                </div>
                <span className="text-sm font-medium text-gray-900">
                  {count}
                  {status === "bycatch" && " ⚠️"}
                  {status === "protected" && " 🚨"}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/components/CatchCounter.tsx
git commit -m "feat(frontend): add CatchCounter component with status indicators"
```

---

### Task 13: Create AlertFeed Component

**Files:**
- Create: `frontend/components/AlertFeed.tsx`

**Step 1: Write AlertFeed.tsx**

```typescript
// frontend/components/AlertFeed.tsx
"use client";

import type { Alert } from "@/lib/types";

interface AlertFeedProps {
  alerts: Alert[];
}

export function AlertFeed({ alerts }: AlertFeedProps) {
  // Show most recent first
  const sortedAlerts = [...alerts].reverse();

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-semibold mb-3 text-gray-800">Alert Feed</h2>

      {sortedAlerts.length === 0 ? (
        <p className="text-gray-500 text-sm">No alerts</p>
      ) : (
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {sortedAlerts.map((alert, index) => {
            const time = new Date(alert.timestamp).toLocaleTimeString();
            return (
              <div
                key={`${alert.timestamp}-${index}`}
                className={`
                  flex items-start gap-2 text-sm p-2 rounded
                  ${alert.level === "info" ? "bg-gray-50" : ""}
                  ${alert.level === "warning" ? "bg-yellow-50" : ""}
                  ${alert.level === "critical" ? "bg-red-50" : ""}
                `}
              >
                <span className="text-gray-400 text-xs whitespace-nowrap">
                  {time}
                </span>
                <span
                  className={`
                    ${alert.level === "info" ? "text-gray-600" : ""}
                    ${alert.level === "warning" ? "text-yellow-700" : ""}
                    ${alert.level === "critical" ? "text-red-700 font-medium" : ""}
                  `}
                >
                  {alert.level === "warning" && "⚠️ "}
                  {alert.level === "critical" && "🚨 "}
                  {alert.message}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/components/AlertFeed.tsx
git commit -m "feat(frontend): add AlertFeed component with severity styling"
```

---

### Task 14: Create ComplianceSummary Component

**Files:**
- Create: `frontend/components/ComplianceSummary.tsx`

**Step 1: Write ComplianceSummary.tsx**

```typescript
// frontend/components/ComplianceSummary.tsx
"use client";

import type { Compliance } from "@/lib/types";

interface ComplianceSummaryProps {
  compliance: Compliance;
}

export function ComplianceSummary({ compliance }: ComplianceSummaryProps) {
  const isCompliant = compliance.status === "COMPLIANT";

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h2 className="text-lg font-semibold mb-3 text-gray-800">Compliance</h2>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Total Catch</span>
          <span className="font-medium">{compliance.total}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Legal</span>
          <span className="font-medium text-green-600">{compliance.legal}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Bycatch</span>
          <span className="font-medium text-yellow-600">{compliance.bycatch}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Protected</span>
          <span className="font-medium text-red-600">{compliance.protected}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Released</span>
          <span className="font-medium">{compliance.released}</span>
        </div>

        <div className="border-t pt-2 mt-2">
          <div
            className={`
              flex items-center justify-center gap-2 py-2 rounded-lg font-medium
              ${isCompliant ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}
            `}
          >
            {isCompliant ? "✓" : "⚠"} {compliance.status.replace("_", " ")}
          </div>
        </div>
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/components/ComplianceSummary.tsx
git commit -m "feat(frontend): add ComplianceSummary component with status badge"
```

---

### Task 15: Create ReleaseButton Component

**Files:**
- Create: `frontend/components/ReleaseButton.tsx`

**Step 1: Write ReleaseButton.tsx**

```typescript
// frontend/components/ReleaseButton.tsx
"use client";

import { useState } from "react";
import { releaseLastCatch } from "@/lib/api";

interface ReleaseButtonProps {
  hasUnreleased: boolean;
  onRelease: () => void;
}

export function ReleaseButton({ hasUnreleased, onRelease }: ReleaseButtonProps) {
  const [isReleasing, setIsReleasing] = useState(false);

  const handleRelease = async () => {
    setIsReleasing(true);
    try {
      await releaseLastCatch();
      onRelease();
    } catch (error) {
      console.error("Release failed:", error);
      alert("Failed to release catch");
    } finally {
      setIsReleasing(false);
    }
  };

  if (!hasUnreleased) {
    return null;
  }

  return (
    <button
      onClick={handleRelease}
      disabled={isReleasing}
      className={`
        w-full py-3 px-4 rounded-lg font-medium text-white
        transition-colors duration-200
        ${isReleasing
          ? "bg-gray-400 cursor-not-allowed"
          : "bg-blue-600 hover:bg-blue-700 active:bg-blue-800"
        }
      `}
    >
      {isReleasing ? (
        <span className="flex items-center justify-center gap-2">
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          Releasing...
        </span>
      ) : (
        "🔓 Mark as Released"
      )}
    </button>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/components/ReleaseButton.tsx
git commit -m "feat(frontend): add ReleaseButton component"
```

---

### Task 16: Build Main Dashboard Page

**Files:**
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/app/layout.tsx`

**Step 1: Update layout.tsx**

```typescript
// frontend/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CatchLog - Fishing Compliance Monitor",
  description: "On-device AI for fishing vessel compliance",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-100 min-h-screen`}>
        {children}
      </body>
    </html>
  );
}
```

**Step 2: Write page.tsx**

```typescript
// frontend/app/page.tsx
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getState, getAudioUrl } from "@/lib/api";
import type { AppState, Detection } from "@/lib/types";

import { ImageUpload } from "@/components/ImageUpload";
import { VideoFeed } from "@/components/VideoFeed";
import { CatchCounter } from "@/components/CatchCounter";
import { AlertFeed } from "@/components/AlertFeed";
import { ComplianceSummary } from "@/components/ComplianceSummary";
import { ReleaseButton } from "@/components/ReleaseButton";

const INITIAL_STATE: AppState = {
  last_detection: null,
  frame_base64: null,
  counts: {},
  alerts: [],
  compliance: {
    total: 0,
    legal: 0,
    bycatch: 0,
    protected: 0,
    released: 0,
    status: "COMPLIANT",
  },
};

export default function Dashboard() {
  const [state, setState] = useState<AppState>(INITIAL_STATE);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Refresh state from backend
  const refreshState = useCallback(async () => {
    try {
      const newState = await getState();
      setState(newState);
    } catch (error) {
      console.error("Failed to refresh state:", error);
    }
  }, []);

  // Handle new detection
  const handleDetection = useCallback(
    (detection: Detection) => {
      // Play audio alert if present
      if (detection.audio_url && audioRef.current) {
        audioRef.current.src = getAudioUrl(detection.audio_url);
        audioRef.current.play().catch(console.error);
      }

      // Refresh full state
      refreshState();
    },
    [refreshState]
  );

  // Check if there are unreleased bycatch/protected
  const hasUnreleased =
    state.compliance.bycatch + state.compliance.protected > state.compliance.released;

  // Initial load
  useEffect(() => {
    refreshState();
  }, [refreshState]);

  return (
    <div className="max-w-6xl mx-auto p-4">
      {/* Header */}
      <header className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">
          🐟 CatchLog
        </h1>
        <div className="w-64">
          <ImageUpload onDetection={handleDetection} />
        </div>
      </header>

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left column: Video feed */}
        <div className="lg:col-span-2 space-y-4">
          <VideoFeed
            frameBase64={state.frame_base64}
            species={state.last_detection?.species}
            status={state.last_detection?.status}
          />
          <ReleaseButton
            hasUnreleased={hasUnreleased}
            onRelease={refreshState}
          />
        </div>

        {/* Right column: Stats */}
        <div className="space-y-4">
          <CatchCounter counts={state.counts} />
          <ComplianceSummary compliance={state.compliance} />
        </div>
      </div>

      {/* Alert feed */}
      <div className="mt-4">
        <AlertFeed alerts={state.alerts} />
      </div>

      {/* Hidden audio element for alerts */}
      <audio ref={audioRef} className="hidden" />
    </div>
  );
}
```

**Step 3: Verify build**

```bash
cd frontend && bun run build
```

Expected: Build succeeds.

**Step 4: Commit**

```bash
git add frontend/app/
git commit -m "feat(frontend): build main dashboard page with all components"
```

---

### Task 17: Create Environment Config

**Files:**
- Create: `frontend/.env.local`
- Update: `frontend/.gitignore`

**Step 1: Create .env.local**

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Step 2: Add .env.example for documentation**

```bash
# frontend/.env.example
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Step 3: Commit example (not .env.local)**

```bash
git add frontend/.env.example
git commit -m "docs(frontend): add environment config example"
```

---

## Phase 3: Integration

### Task 18: End-to-End Test

**Step 1: Start backend**

```bash
cd backend && uv run uvicorn main:app --reload --port 8000
```

**Step 2: Start frontend (new terminal)**

```bash
cd frontend && bun run dev
```

**Step 3: Manual test checklist**

Open http://localhost:3000 and verify:

- [ ] Dashboard loads with empty state
- [ ] Upload an image → detection appears
- [ ] Bounding box drawn on image
- [ ] Catch counter updates
- [ ] If bycatch/protected: alert appears, audio plays
- [ ] Release button appears for bycatch/protected
- [ ] Click release → compliance updates
- [ ] Multiple uploads accumulate counts

**Step 4: Clean up test data**

```bash
rm -f backend/catch_log.db
```

---

### Task 19: Add Audio Placeholder Files

**Files:**
- Create: `backend/audio/alert_info.mp3`
- Create: `backend/audio/alert_warning.mp3`
- Create: `backend/audio/alert_critical.mp3`

**Step 1: Create placeholder audio files**

For now, create empty placeholder files. Replace with real ElevenLabs audio later.

```bash
# Create 1-second silent MP3 placeholders (or download real ones)
# For hackathon: can use any short audio files or generate via ElevenLabs

touch backend/audio/alert_info.mp3
touch backend/audio/alert_warning.mp3
touch backend/audio/alert_critical.mp3
```

**Note:** Replace these with actual audio files generated from ElevenLabs:
- `alert_info.mp3`: "Catch logged. Species recorded."
- `alert_warning.mp3`: "Bycatch detected. Release required."
- `alert_critical.mp3`: "Alert. Protected species. Immediate release required."

**Step 2: Commit**

```bash
git add backend/audio/
git commit -m "chore(backend): add audio placeholder files"
```

---

## Summary

**Backend files created:**
- `backend/pyproject.toml` - Project config
- `backend/models.py` - Pydantic schemas
- `backend/database.py` - SQLite operations
- `backend/inference.py` - Mock inference (swap later)
- `backend/agent.py` - Detection pipeline
- `backend/main.py` - FastAPI routes
- `backend/tests/test_api.py` - Integration tests

**Frontend files created:**
- `frontend/` - Next.js 14 app
- `frontend/lib/types.ts` - TypeScript types
- `frontend/lib/api.ts` - API client
- `frontend/components/ImageUpload.tsx`
- `frontend/components/VideoFeed.tsx`
- `frontend/components/CatchCounter.tsx`
- `frontend/components/AlertFeed.tsx`
- `frontend/components/ComplianceSummary.tsx`
- `frontend/components/ReleaseButton.tsx`
- `frontend/app/page.tsx` - Main dashboard

**To swap in real model:**
1. Update `backend/inference.py` with PaliGemma loading
2. Replace `run_inference()` implementation
3. No other changes needed

---

**Estimated time:** 2-3 hours for experienced developer

**Next:** Generate ElevenLabs audio files, then integrate real model when ready.
