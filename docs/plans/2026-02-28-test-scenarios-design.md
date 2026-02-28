# CatchLog Test Scenarios Design

**Date:** 2026-02-28
**Purpose:** Backend scenario tests + Manual UI testing guide
**Constraint:** Species updated to match FOID dataset findings

---

## Part 1: Species Updates

### Current vs Updated Species List

Based on data exploration findings, update species to match the actual FOID dataset:

| ID | Current | Updated | Status | Reason |
|----|---------|---------|--------|--------|
| 1 | Albacore Tuna | Albacore Tuna | legal | Keep |
| 2 | Bigeye Tuna | Bigeye Tuna | legal | Keep |
| 3 | Mahi-Mahi | Mahi-Mahi | legal | Keep |
| 4 | Blue Shark | **Shark** | bycatch | Dataset uses generic "Shark" |
| 5 | Sea Turtle | **Pelagic Stingray** | protected | Sea Turtle NOT in dataset |
| 6 | Unknown | Unknown | unknown | Keep |
| 7 | - | **Yellowfin Tuna** | legal | Add - abundant in dataset |
| 8 | - | **Opah** | bycatch | Add - common bycatch |

### Files to Update

**backend/database.py:**
```python
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

**backend/inference.py:**
```python
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

**frontend/components/CatchCounter.tsx:**
```typescript
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

---

## Part 2: Backend Scenario Tests

### Test Infrastructure

Add test control to `backend/inference.py`:

```python
# Test-only: force specific species for deterministic testing
_forced_species: str | None = None

def set_next_species(species: str | None) -> None:
    """Force next inference to return specific species. For testing only."""
    global _forced_species
    _forced_species = species

def run_inference(image: Image.Image) -> InferenceResult:
    global _forced_species

    # If species is forced (testing), use it
    if _forced_species:
        species = _forced_species
        _forced_species = None  # Reset after use
    else:
        species = _weighted_random_species()

    # ... rest of function
```

### Test Scenarios

Create `backend/tests/test_scenarios.py`:

#### Scenario 1: Legal Catch Flow
```python
def test_legal_catch_flow(client, test_image):
    """Legal fish: no alert, stays COMPLIANT."""
    set_next_species("Albacore Tuna")

    response = client.post("/api/upload", files={"file": ("test.jpg", test_image, "image/jpeg")})
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
```

#### Scenario 2: Bycatch Detection
```python
def test_bycatch_detection(client, test_image):
    """Bycatch: warning alert, ACTION_REQUIRED."""
    set_next_species("Shark")

    response = client.post("/api/upload", files={"file": ("test.jpg", test_image, "image/jpeg")})
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
```

#### Scenario 3: Protected Species Detection
```python
def test_protected_species_detection(client, test_image):
    """Protected species: critical alert, ACTION_REQUIRED."""
    set_next_species("Pelagic Stingray")

    response = client.post("/api/upload", files={"file": ("test.jpg", test_image, "image/jpeg")})
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
```

#### Scenario 4: Release Bycatch Flow
```python
def test_release_bycatch_flow(client, test_image):
    """Release bycatch: compliance returns to COMPLIANT."""
    set_next_species("Shark")

    # Upload bycatch
    client.post("/api/upload", files={"file": ("test.jpg", test_image, "image/jpeg")})

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
```

#### Scenario 5: Multiple Legal Catches
```python
def test_multiple_legal_catches(client, test_image):
    """Multiple legal catches accumulate correctly."""
    species_to_upload = ["Albacore Tuna", "Yellowfin Tuna", "Albacore Tuna"]

    for species in species_to_upload:
        set_next_species(species)
        client.post("/api/upload", files={"file": ("test.jpg", test_image, "image/jpeg")})

    state = client.get("/api/state").json()

    assert state["compliance"]["total"] == 3
    assert state["compliance"]["legal"] == 3
    assert state["compliance"]["status"] == "COMPLIANT"
    assert state["counts"]["Albacore Tuna"] == 2
    assert state["counts"]["Yellowfin Tuna"] == 1
```

#### Scenario 6: Mixed Compliance Flow
```python
def test_mixed_compliance_flow(client, test_image):
    """Mixed catches: legal + bycatch, then release."""
    # Upload 2 legal
    set_next_species("Albacore Tuna")
    client.post("/api/upload", files={"file": ("test.jpg", test_image, "image/jpeg")})
    set_next_species("Yellowfin Tuna")
    client.post("/api/upload", files={"file": ("test.jpg", test_image, "image/jpeg")})

    # Verify still COMPLIANT
    state = client.get("/api/state").json()
    assert state["compliance"]["status"] == "COMPLIANT"

    # Upload bycatch
    set_next_species("Opah")
    client.post("/api/upload", files={"file": ("test.jpg", test_image, "image/jpeg")})

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
```

#### Scenario 7: Release When Already Compliant
```python
def test_release_when_compliant(client, test_image):
    """Release with nothing to release returns 404."""
    # Upload legal fish only
    set_next_species("Albacore Tuna")
    client.post("/api/upload", files={"file": ("test.jpg", test_image, "image/jpeg")})

    # Try to release
    response = client.post("/api/release")
    assert response.status_code == 404
```

#### Scenario 8: Unknown Species
```python
def test_unknown_species(client, test_image):
    """Unknown species: info alert, stays COMPLIANT."""
    set_next_species("Unknown")

    response = client.post("/api/upload", files={"file": ("test.jpg", test_image, "image/jpeg")})
    data = response.json()

    assert data["species"] == "Unknown"
    assert data["status"] == "unknown"
    assert data["alert_level"] == "info"

    # Unknown doesn't require action - stays COMPLIANT
    state = client.get("/api/state").json()
    assert state["compliance"]["status"] == "COMPLIANT"
```

---

## Part 3: Manual UI Testing Guide

### Prerequisites

1. Start backend: `cd backend && uv run uvicorn main:app --reload --port 8000`
2. Start frontend: `cd frontend && bun run dev`
3. Open browser: http://localhost:3000
4. Have test images ready from FOID dataset (or use mock inference)

### Test Images Location

Use images from: `/Users/misran/Documents/misu/instalily-ai-hackathon/catchlog/data/images/`

Or download specific test images:
- Legal: Any Albacore/Yellowfin/Bigeye image
- Bycatch: Shark or Opah image
- Protected: Pelagic Stingray image

---

### UI Test 1: Initial State

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | Open http://localhost:3000 | Dashboard loads | |
| 2 | Check VideoFeed panel | Shows fish emoji + "No image uploaded yet" | |
| 3 | Check Catch Counter | Shows "No catches recorded" | |
| 4 | Check Compliance panel | Total: 0, Status: "COMPLIANT" (green) | |
| 5 | Check Alert Feed | Shows "No alerts" | |
| 6 | Check for Release button | NOT visible | |

---

### UI Test 2: Legal Catch (Albacore Tuna)

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | Click upload or drag Albacore image | Spinner shows "Processing..." | |
| 2 | Wait for processing | Image appears in VideoFeed | |
| 3 | Check bounding box color | **GREEN** rectangle around fish | |
| 4 | Check species badge | "Albacore Tuna" pill in green at bottom-left | |
| 5 | Check Catch Counter | "Albacore Tuna: 1" with green dot | |
| 6 | Check Compliance | Total: 1, Legal: 1, Status: **COMPLIANT** (green) | |
| 7 | Check Alert Feed | Still shows "No alerts" | |
| 8 | Check Release button | NOT visible | |
| 9 | Check audio | NO sound plays | |

---

### UI Test 3: Bycatch Detection (Shark)

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | Upload Shark image | Processing spinner | |
| 2 | Check bounding box color | **YELLOW** rectangle | |
| 3 | Check species badge | "Shark" pill in yellow | |
| 4 | Check Catch Counter | "Shark: 1" with yellow dot + ⚠️ emoji | |
| 5 | Check Compliance | Status: **ACTION REQUIRED** (red background) | |
| 6 | Check Alert Feed | New entry: "⚠️ BYCATCH: Shark — Release required" | |
| 7 | Check alert background | Yellow/amber background on alert | |
| 8 | Check Release button | **VISIBLE** - blue "🔓 Mark as Released" | |
| 9 | Check audio | Warning sound plays (if audio files present) | |

---

### UI Test 4: Protected Species (Pelagic Stingray)

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | Upload Pelagic Stingray image | Processing spinner | |
| 2 | Check bounding box color | **RED** rectangle | |
| 3 | Check species badge | "Pelagic Stingray" pill in red | |
| 4 | Check Catch Counter | "Pelagic Stingray: 1" with red dot + 🚨 emoji | |
| 5 | Check Compliance | Protected: 1, Status: **ACTION REQUIRED** | |
| 6 | Check Alert Feed | "🚨 PROTECTED: Pelagic Stingray — Immediate release required" | |
| 7 | Check alert background | Red/pink background on alert | |
| 8 | Check Release button | **VISIBLE** | |
| 9 | Check audio | Critical alert sound plays | |

---

### UI Test 5: Release Flow

**Prerequisite:** Complete UI Test 3 (Shark uploaded, ACTION_REQUIRED)

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | Click "🔓 Mark as Released" | Button shows spinner "Releasing..." | |
| 2 | Wait for completion | Button disappears | |
| 3 | Check Compliance | Released: 1, Status: **COMPLIANT** (green) | |
| 4 | Check Catch Counter | "Shark: 1" still visible (count preserved) | |
| 5 | Try clicking release again | Button not visible (nothing to release) | |

---

### UI Test 6: Multiple Uploads

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | Upload 3 different fish images | Each processes successfully | |
| 2 | Check VideoFeed | Shows LAST uploaded image only | |
| 3 | Check Catch Counter | Shows all species with counts | |
| 4 | Check counts sorted | Highest count at top | |
| 5 | Check Compliance total | Total matches number of uploads | |

---

### UI Test 7: Mixed Scenario (Full Demo Flow)

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | Fresh start (restart backend to clear DB) | Empty state | |
| 2 | Upload Albacore | Legal: 1, COMPLIANT | |
| 3 | Upload Yellowfin | Legal: 2, COMPLIANT | |
| 4 | Upload Shark | Bycatch: 1, ACTION_REQUIRED, alert shows | |
| 5 | Click Release | Released: 1, COMPLIANT | |
| 6 | Upload Pelagic Stingray | Protected: 1, ACTION_REQUIRED, critical alert | |
| 7 | Click Release | Released: 2, COMPLIANT | |
| 8 | Final state | Total: 4, Legal: 2, Bycatch: 1, Protected: 1, Released: 2 | |

---

### UI Test 8: Error Handling

| Step | Action | Expected Result | Pass? |
|------|--------|-----------------|-------|
| 1 | Upload non-image file (.txt, .pdf) | Alert: "Please upload an image file" | |
| 2 | Upload corrupted image | Alert: "Failed to upload image" | |
| 3 | Stop backend, try upload | Alert: "Failed to upload image" (network error) | |

---

## Visual Reference: Expected UI States

### COMPLIANT State
```
┌─────────────────────────────────────────────────────────────────┐
│  🐟 CatchLog                                    [Upload Image]  │
├───────────────────────────────────┬─────────────────────────────┤
│                                   │   CATCH COUNTER             │
│   [Image with GREEN bbox]         │   ● Albacore Tuna    3      │
│   ┌─────────────────────┐         │   ● Yellowfin Tuna   2      │
│   │    🟢 Albacore Tuna │         ├─────────────────────────────┤
│   └─────────────────────┘         │   COMPLIANCE                │
│                                   │   Total: 5 | Legal: 5       │
│   (no release button)             │   ┌─────────────────────┐   │
│                                   │   │  ✓ COMPLIANT        │   │
│                                   │   └─────────────────────┘   │
├───────────────────────────────────┴─────────────────────────────┤
│   ALERT FEED                                                    │
│   No alerts                                                     │
└─────────────────────────────────────────────────────────────────┘
```

### ACTION_REQUIRED State (Bycatch)
```
┌─────────────────────────────────────────────────────────────────┐
│  🐟 CatchLog                                    [Upload Image]  │
├───────────────────────────────────┬─────────────────────────────┤
│                                   │   CATCH COUNTER             │
│   [Image with YELLOW bbox]        │   ● Albacore Tuna    3      │
│   ┌─────────────────────┐         │   ● Shark            1 ⚠️   │
│   │    🟡 Shark         │         ├─────────────────────────────┤
│   └─────────────────────┘         │   COMPLIANCE                │
│                                   │   Total: 4 | Bycatch: 1     │
│   ┌─────────────────────────┐     │   ┌─────────────────────┐   │
│   │ 🔓 Mark as Released     │     │   │  ⚠ ACTION REQUIRED  │   │
│   └─────────────────────────┘     │   └─────────────────────┘   │
├───────────────────────────────────┴─────────────────────────────┤
│   ALERT FEED                                                    │
│   14:23:45  ⚠️ BYCATCH: Shark — Release required               │
└─────────────────────────────────────────────────────────────────┘
```

### ACTION_REQUIRED State (Protected)
```
┌─────────────────────────────────────────────────────────────────┐
│  🐟 CatchLog                                    [Upload Image]  │
├───────────────────────────────────┬─────────────────────────────┤
│                                   │   CATCH COUNTER             │
│   [Image with RED bbox]           │   ● Albacore Tuna    3      │
│   ┌─────────────────────────┐     │   ● Pelagic Stingray 1 🚨   │
│   │ 🔴 Pelagic Stingray     │     ├─────────────────────────────┤
│   └─────────────────────────┘     │   COMPLIANCE                │
│                                   │   Total: 4 | Protected: 1   │
│   ┌─────────────────────────┐     │   ┌─────────────────────┐   │
│   │ 🔓 Mark as Released     │     │   │  ⚠ ACTION REQUIRED  │   │
│   └─────────────────────────┘     │   └─────────────────────┘   │
├───────────────────────────────────┴─────────────────────────────┤
│   ALERT FEED                                                    │
│   14:24:12  🚨 PROTECTED: Pelagic Stingray — Immediate release  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary

### Backend Tests (8 scenarios)
1. Legal catch flow
2. Bycatch detection
3. Protected species detection
4. Release bycatch flow
5. Multiple legal catches
6. Mixed compliance flow
7. Release when already compliant
8. Unknown species

### Manual UI Tests (8 scenarios)
1. Initial state
2. Legal catch
3. Bycatch detection
4. Protected species
5. Release flow
6. Multiple uploads
7. Mixed scenario (full demo)
8. Error handling

### Files to Create/Modify
- `backend/database.py` - Update SPECIES_DATA
- `backend/inference.py` - Update SPECIES_WEIGHTS, add set_next_species()
- `backend/tests/test_scenarios.py` - New file with 8 scenario tests
- `frontend/components/CatchCounter.tsx` - Update SPECIES_STATUS mapping
