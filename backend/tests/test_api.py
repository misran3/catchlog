# backend/tests/test_api.py
"""Integration tests for CatchLog API."""

import pytest
from fastapi.testclient import TestClient
from PIL import Image
import io

from main import app
from database import init_db, reset_db
from agent import reset_state


@pytest.fixture(autouse=True)
def clean_state():
    """Reset state before each test."""
    init_db()
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
