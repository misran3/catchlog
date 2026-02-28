# Test Scenarios Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Update species to match FOID dataset and add 8 backend scenario tests with deterministic test control.

**Architecture:** Update species data in 3 files (database, inference, frontend), add `set_next_species()` to inference for test control, create comprehensive scenario tests.

**Tech Stack:** Python/pytest (backend), TypeScript (frontend)

---

## Task 1: Update Species in Database

**Files:**
- Modify: `backend/database.py:11-18`

**Step 1: Update SPECIES_DATA**

Replace the current SPECIES_DATA (lines 11-18) with:

```python
# Species seed data: (id, name, status)
# Status: 0=legal, 1=bycatch, 2=protected, 3=unknown
SPECIES_DATA = [
    (1, "Albacore Tuna", 0),      # legal
    (2, "Bigeye Tuna", 0),        # legal
    (3, "Mahi-Mahi", 0),          # legal
    (4, "Yellowfin Tuna", 0),     # legal (new)
    (5, "Shark", 1),              # bycatch (was Blue Shark)
    (6, "Opah", 1),               # bycatch (new)
    (7, "Pelagic Stingray", 2),   # protected (was Sea Turtle)
    (8, "Unknown", 3),            # unknown
]
```

**Step 2: Delete old database to force reseed**

```bash
rm -f backend/catch_log.db
```

**Step 3: Verify species load correctly**

```bash
cd backend && uv run python -c "
from database import init_db, get_all_species
init_db()
species = get_all_species()
print(f'Species count: {len(species)}')
for s in species:
    print(f'  {s[\"id\"]}: {s[\"name\"]} (status={s[\"status\"]})')
"
```

Expected output:
```
Species count: 8
  1: Albacore Tuna (status=0)
  2: Bigeye Tuna (status=0)
  3: Mahi-Mahi (status=0)
  4: Yellowfin Tuna (status=0)
  5: Shark (status=1)
  6: Opah (status=1)
  7: Pelagic Stingray (status=2)
  8: Unknown (status=3)
```

**Step 4: Commit**

```bash
rm -f backend/catch_log.db
git add backend/database.py
git commit -m "feat(backend): update species to match FOID dataset"
```

---

## Task 2: Update Species Weights and Add Test Control to Inference

**Files:**
- Modify: `backend/inference.py`

**Step 1: Update SPECIES_WEIGHTS (replace lines 17-26)**

```python
# Weighted species distribution for realistic demo
# Format: (species_name, weight)
SPECIES_WEIGHTS = [
    ("Albacore Tuna", 35),    # Legal - most common
    ("Yellowfin Tuna", 20),   # Legal - common
    ("Bigeye Tuna", 10),      # Legal
    ("Mahi-Mahi", 5),         # Legal
    ("Shark", 15),            # Bycatch
    ("Opah", 8),              # Bycatch
    ("Pelagic Stingray", 5),  # Protected - rare
    ("Unknown", 2),           # Unknown - very rare
]
```

**Step 2: Add test control (insert after SPECIES_WEIGHTS, before _weighted_random_species)**

```python
# Test-only: force specific species for deterministic testing
_forced_species: str | None = None


def set_next_species(species: str | None) -> None:
    """Force next inference to return specific species. For testing only."""
    global _forced_species
    _forced_species = species
```

**Step 3: Update run_inference to use forced species (modify lines 51-68)**

```python
def run_inference(image: Image.Image) -> InferenceResult:
    """
    Run mock inference on an image.

    In production, this would:
    1. Preprocess image for PaliGemma
    2. Run model forward pass
    3. Parse detection output

    For now, returns random realistic results.
    """
    global _forced_species

    width, height = image.size

    # Use forced species if set (for testing), otherwise random
    if _forced_species:
        species = _forced_species
        _forced_species = None  # Reset after use
    else:
        species = _weighted_random_species()

    return InferenceResult(
        species=species,
        confidence=round(random.uniform(0.75, 0.98), 2),
        bbox=_random_bbox(width, height),
    )
```

**Step 4: Test the new functionality**

```bash
cd backend && uv run python -c "
from inference import run_inference, set_next_species, load_model
from PIL import Image

load_model()
img = Image.new('RGB', (640, 480), color='blue')

# Test forced species
set_next_species('Shark')
result = run_inference(img)
print(f'Forced species: {result.species}')
assert result.species == 'Shark', 'Forced species failed'

# Test auto-reset (should be random now)
result2 = run_inference(img)
print(f'Random species: {result2.species}')

print('Test passed!')
"
```

Expected: First returns "Shark", second returns random species.

**Step 5: Commit**

```bash
git add backend/inference.py
git commit -m "feat(backend): update species weights and add set_next_species for testing"
```

---

## Task 3: Update Frontend Species Mapping

**Files:**
- Modify: `frontend/components/CatchCounter.tsx:9-16`

**Step 1: Update SPECIES_STATUS mapping**

Replace lines 9-16 with:

```typescript
// Map species to their status for styling
const SPECIES_STATUS: Record<string, "legal" | "bycatch" | "protected" | "unknown"> = {
  "Albacore Tuna": "legal",
  "Bigeye Tuna": "legal",
  "Mahi-Mahi": "legal",
  "Yellowfin Tuna": "legal",
  "Shark": "bycatch",
  "Opah": "bycatch",
  "Pelagic Stingray": "protected",
  "Unknown": "unknown",
};
```

**Step 2: Verify build**

```bash
cd frontend && bun run build
```

Expected: Build succeeds.

**Step 3: Commit**

```bash
git add frontend/components/CatchCounter.tsx
git commit -m "feat(frontend): update species mapping to match FOID dataset"
```

---

## Task 4: Create Scenario Tests File

**Files:**
- Create: `backend/tests/test_scenarios.py`

**Step 1: Create test file with all 8 scenarios**

```python
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
```

**Step 2: Commit**

```bash
git add backend/tests/test_scenarios.py
git commit -m "test(backend): add 8 scenario tests for compliance flows"
```

---

## Task 5: Run All Tests

**Step 1: Run the original tests**

```bash
cd backend && uv run pytest tests/test_api.py -v
```

Expected: 6 tests pass.

**Step 2: Run the new scenario tests**

```bash
cd backend && uv run pytest tests/test_scenarios.py -v
```

Expected: 8 tests pass.

**Step 3: Run all tests together**

```bash
cd backend && uv run pytest tests/ -v
```

Expected: 14 tests pass (6 original + 8 scenarios).

**Step 4: Clean up**

```bash
rm -f backend/catch_log.db
```

---

## Summary

**Files Modified:**
| File | Change |
|------|--------|
| `backend/database.py` | Updated SPECIES_DATA (6 → 8 species) |
| `backend/inference.py` | Updated weights + added `set_next_species()` |
| `frontend/components/CatchCounter.tsx` | Updated SPECIES_STATUS mapping |

**Files Created:**
| File | Content |
|------|---------|
| `backend/tests/test_scenarios.py` | 8 scenario tests |

**Test Coverage:**
| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_api.py` | 6 | Basic API endpoints |
| `test_scenarios.py` | 8 | Compliance flow scenarios |
| **Total** | **14** | |

**Species Changes:**
| Old | New | Status |
|-----|-----|--------|
| Blue Shark | Shark | bycatch |
| Sea Turtle | Pelagic Stingray | protected |
| - | Yellowfin Tuna | legal |
| - | Opah | bycatch |
