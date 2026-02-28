# backend/tests/test_scenarios.py
"""Scenario tests for CatchLog compliance flows."""

import pytest
from fastapi.testclient import TestClient
from PIL import Image
import io

from main import app
from database import init_db, reset_db
from agent import reset_state
from inference import set_next_species


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


# === Scenario 1: Legal Catch Flow ===

def test_legal_catch_flow(client, test_image):
    """Legal fish: no alert, stays COMPLIANT."""
    set_next_species("Albacore Tuna")

    response = client.post(
        "/api/upload",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )
    data = response.json()

    assert data["species"] == "Albacore Tuna"
    assert data["status"] == "legal"
    assert data["alert_level"] == "none"
    assert data["audio_url"] is None

    # Check compliance
    state = client.get("/api/state").json()
    assert state["compliance"]["status"] == "COMPLIANT"
    assert state["compliance"]["legal"] == 1
    assert len(state["alerts"]) == 0


# === Scenario 2: Bycatch Detection ===

def test_bycatch_detection(client, test_image):
    """Bycatch: warning alert, ACTION_REQUIRED."""
    set_next_species("Shark")

    response = client.post(
        "/api/upload",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )
    data = response.json()

    assert data["species"] == "Shark"
    assert data["status"] == "bycatch"
    assert data["alert_level"] == "warning"
    assert data["audio_url"] == "/audio/alert_warning.mp3"

    # Check compliance
    state = client.get("/api/state").json()
    assert state["compliance"]["status"] == "ACTION_REQUIRED"
    assert state["compliance"]["bycatch"] == 1
    assert len(state["alerts"]) == 1
    assert "BYCATCH" in state["alerts"][0]["message"]


# === Scenario 3: Protected Species Detection ===

def test_protected_species_detection(client, test_image):
    """Protected species: critical alert, ACTION_REQUIRED."""
    set_next_species("Pelagic Stingray")

    response = client.post(
        "/api/upload",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )
    data = response.json()

    assert data["species"] == "Pelagic Stingray"
    assert data["status"] == "protected"
    assert data["alert_level"] == "critical"
    assert data["audio_url"] == "/audio/alert_critical.mp3"

    # Check compliance
    state = client.get("/api/state").json()
    assert state["compliance"]["status"] == "ACTION_REQUIRED"
    assert state["compliance"]["protected"] == 1
    assert len(state["alerts"]) == 1
    assert "PROTECTED" in state["alerts"][0]["message"]


# === Scenario 4: Release Bycatch Flow ===

def test_release_bycatch_flow(client, test_image):
    """Release bycatch: compliance returns to COMPLIANT."""
    set_next_species("Shark")

    # Upload bycatch
    client.post(
        "/api/upload",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )

    # Verify ACTION_REQUIRED
    state = client.get("/api/state").json()
    assert state["compliance"]["status"] == "ACTION_REQUIRED"

    # Release
    release_response = client.post("/api/release")
    assert release_response.status_code == 200
    release_data = release_response.json()
    assert release_data["species"] == "Shark"
    assert release_data["compliance_status"] == "COMPLIANT"

    # Verify COMPLIANT
    state = client.get("/api/state").json()
    assert state["compliance"]["status"] == "COMPLIANT"
    assert state["compliance"]["released"] == 1


# === Scenario 5: Multiple Legal Catches ===

def test_multiple_legal_catches(client, test_image):
    """Multiple legal catches accumulate correctly."""
    species_to_upload = ["Albacore Tuna", "Yellowfin Tuna", "Albacore Tuna"]

    for species in species_to_upload:
        set_next_species(species)
        client.post(
            "/api/upload",
            files={"file": ("test.jpg", test_image, "image/jpeg")}
        )

    state = client.get("/api/state").json()

    assert state["compliance"]["total"] == 3
    assert state["compliance"]["legal"] == 3
    assert state["compliance"]["status"] == "COMPLIANT"
    assert state["counts"]["Albacore Tuna"] == 2
    assert state["counts"]["Yellowfin Tuna"] == 1


# === Scenario 6: Mixed Compliance Flow ===

def test_mixed_compliance_flow(client, test_image):
    """Mixed catches: legal + bycatch, then release."""
    # Upload 2 legal
    set_next_species("Albacore Tuna")
    client.post(
        "/api/upload",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )
    set_next_species("Yellowfin Tuna")
    client.post(
        "/api/upload",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )

    # Verify still COMPLIANT
    state = client.get("/api/state").json()
    assert state["compliance"]["status"] == "COMPLIANT"

    # Upload bycatch
    set_next_species("Opah")
    client.post(
        "/api/upload",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )

    # Verify ACTION_REQUIRED
    state = client.get("/api/state").json()
    assert state["compliance"]["status"] == "ACTION_REQUIRED"
    assert state["compliance"]["total"] == 3
    assert state["compliance"]["bycatch"] == 1

    # Release
    client.post("/api/release")

    # Verify back to COMPLIANT
    state = client.get("/api/state").json()
    assert state["compliance"]["status"] == "COMPLIANT"
    assert state["compliance"]["released"] == 1


# === Scenario 7: Release When Already Compliant ===

def test_release_when_compliant(client, test_image):
    """Release with nothing to release returns 404."""
    # Upload legal fish only
    set_next_species("Albacore Tuna")
    client.post(
        "/api/upload",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )

    # Try to release
    response = client.post("/api/release")
    assert response.status_code == 404


# === Scenario 8: Unknown Species ===

def test_unknown_species(client, test_image):
    """Unknown species: info alert, stays COMPLIANT."""
    set_next_species("Unknown")

    response = client.post(
        "/api/upload",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )
    data = response.json()

    assert data["species"] == "Unknown"
    assert data["status"] == "unknown"
    assert data["alert_level"] == "info"

    # Unknown doesn't require action - stays COMPLIANT
    state = client.get("/api/state").json()
    assert state["compliance"]["status"] == "COMPLIANT"
