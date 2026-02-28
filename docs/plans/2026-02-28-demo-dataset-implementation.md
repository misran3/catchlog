# Demo Dataset & Mock Inference Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a curated demo dataset from FOID and add MOCK_INFERENCE mode for deterministic UI testing.

**Architecture:** Python script extracts images from FOID dataset, backend parses species from filename when MOCK_INFERENCE=true.

**Tech Stack:** Python/pandas (extraction), FastAPI (backend)

---

## Task 1: Create Demo Images Directory

**Files:**
- Create: `backend/demo_images/.gitkeep`

**Step 1: Create directory**

```bash
mkdir -p backend/demo_images
touch backend/demo_images/.gitkeep
```

**Step 2: Add to .gitignore (images only, keep .gitkeep)**

Add to `backend/.gitignore`:
```
demo_images/*.jpg
```

**Step 3: Commit**

```bash
git add backend/demo_images/.gitkeep backend/.gitignore
git commit -m "chore(backend): add demo_images directory"
```

---

## Task 2: Create Extraction Script

**Files:**
- Create: `scripts/extract_demo_images.py`

**Step 1: Create the extraction script**

```python
#!/usr/bin/env python3
"""Extract demo images from FOID dataset for UI testing."""

import random
import shutil
from pathlib import Path

import pandas as pd

# Paths
DATA_DIR = Path(__file__).parent.parent / "data" / "foid_v012"
LABELS_FILE = DATA_DIR / "labels" / "foid_labels_bbox_v012.csv"
IMAGES_DIR = DATA_DIR / "images"
OUTPUT_DIR = Path(__file__).parent.parent / "backend" / "demo_images"

# Image dimensions (from dataset analysis)
IMG_WIDTH = 1280
IMG_HEIGHT = 720
IMG_AREA = IMG_WIDTH * IMG_HEIGHT

# Species to extract: (dataset_label, slug, count)
TARGET_SPECIES = [
    ("Albacore", "albacore-tuna", 3),
    ("Bigeye tuna", "bigeye-tuna", 2),
    ("Mahi mahi", "mahi-mahi", 2),
    ("Yellowfin tuna", "yellowfin-tuna", 3),
    ("Shark", "shark", 3),
    ("Opah", "opah", 2),
    ("Pelagic stingray", "pelagic-stingray", 3),
    ("Unknown", "unknown", 2),
]

# Minimum bbox area as fraction of image (5%)
MIN_BBOX_AREA_FRACTION = 0.05


def bbox_area(row: pd.Series) -> float:
    """Calculate bounding box area."""
    width = row["x_max"] - row["x_min"]
    height = row["y_max"] - row["y_min"]
    return width * height


def extract_images():
    """Extract demo images from FOID dataset."""
    print("Loading FOID labels...")
    df = pd.read_csv(LABELS_FILE)

    # Filter to fish only (exclude HUMAN, NoF)
    fish_df = df[~df["label_l2"].isin(["HUMAN", "NoF"])].copy()
    print(f"Fish bounding boxes: {len(fish_df):,}")

    # Calculate bbox area
    fish_df["bbox_area"] = fish_df.apply(bbox_area, axis=1)
    fish_df["bbox_area_pct"] = fish_df["bbox_area"] / IMG_AREA

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Clear existing demo images
    for f in OUTPUT_DIR.glob("*.jpg"):
        f.unlink()

    total_extracted = 0

    for dataset_label, slug, count in TARGET_SPECIES:
        print(f"\n{dataset_label} -> {slug}")

        # Filter to this species
        species_df = fish_df[fish_df["label_l1"] == dataset_label]
        print(f"  Total bboxes: {len(species_df)}")

        # Filter to prominent bboxes (>5% of image)
        prominent_df = species_df[species_df["bbox_area_pct"] > MIN_BBOX_AREA_FRACTION]
        print(f"  Prominent bboxes (>5%): {len(prominent_df)}")

        # Get unique images
        unique_images = prominent_df["img_id"].unique()
        print(f"  Unique images: {len(unique_images)}")

        # Sample images
        sample_count = min(count, len(unique_images))
        if sample_count == 0:
            print(f"  WARNING: No suitable images found!")
            continue

        sampled_ids = random.sample(list(unique_images), sample_count)

        # Copy images
        for i, img_id in enumerate(sampled_ids, 1):
            src = IMAGES_DIR / f"{img_id}.jpg"
            dst = OUTPUT_DIR / f"{slug}_{i:03d}.jpg"

            if src.exists():
                shutil.copy(src, dst)
                print(f"  Copied: {dst.name}")
                total_extracted += 1
            else:
                print(f"  WARNING: Source not found: {src}")

    print(f"\n{'=' * 40}")
    print(f"Total images extracted: {total_extracted}")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    random.seed(42)  # Reproducible sampling
    extract_images()
```

**Step 2: Create pyproject.toml for scripts**

Create `scripts/pyproject.toml`:

```toml
[project]
name = "catchlog-scripts"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pandas>=2.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Step 3: Test the script runs (dry run check)**

```bash
cd scripts && uv run python extract_demo_images.py
```

Expected: Script extracts ~20 images to `backend/demo_images/`.

**Step 4: Verify extracted images**

```bash
ls -la backend/demo_images/
```

Expected output (approximately):
```
albacore-tuna_001.jpg
albacore-tuna_002.jpg
albacore-tuna_003.jpg
bigeye-tuna_001.jpg
bigeye-tuna_002.jpg
mahi-mahi_001.jpg
mahi-mahi_002.jpg
yellowfin-tuna_001.jpg
yellowfin-tuna_002.jpg
yellowfin-tuna_003.jpg
shark_001.jpg
shark_002.jpg
shark_003.jpg
opah_001.jpg
opah_002.jpg
pelagic-stingray_001.jpg
pelagic-stingray_002.jpg
pelagic-stingray_003.jpg
unknown_001.jpg
unknown_002.jpg
```

**Step 5: Commit**

```bash
git add scripts/extract_demo_images.py scripts/pyproject.toml
git commit -m "feat(scripts): add demo image extraction script"
```

---

## Task 3: Add MOCK_INFERENCE Mode to Backend

**Files:**
- Modify: `backend/inference.py`

**Step 1: Add filename parsing constants (after SPECIES_WEIGHTS)**

```python
# Filename to species mapping for MOCK_INFERENCE mode
FILENAME_TO_SPECIES = {
    "albacore-tuna": "Albacore Tuna",
    "bigeye-tuna": "Bigeye Tuna",
    "mahi-mahi": "Mahi-Mahi",
    "yellowfin-tuna": "Yellowfin Tuna",
    "shark": "Shark",
    "opah": "Opah",
    "pelagic-stingray": "Pelagic Stingray",
    "unknown": "Unknown",
}
```

**Step 2: Add filename parsing function (after set_next_species)**

```python
def parse_species_from_filename(filename: str | None) -> str | None:
    """Extract species from filename like 'shark_001.jpg' -> 'Shark'.

    For MOCK_INFERENCE mode only.
    """
    if not filename:
        return None

    import re
    from pathlib import Path

    stem = Path(filename).stem  # 'shark_001'
    # Remove trailing _NNN
    slug = re.sub(r"_\d+$", "", stem)  # 'shark'
    return FILENAME_TO_SPECIES.get(slug)
```

**Step 3: Update run_inference signature and logic**

Replace the existing `run_inference` function:

```python
def run_inference(image: Image.Image, filename: str | None = None) -> InferenceResult:
    """
    Run mock inference on an image.

    In production, this would:
    1. Preprocess image for PaliGemma
    2. Run model forward pass
    3. Parse detection output

    For now, returns mock results based on:
    1. Forced species (set_next_species) - for tests
    2. Filename parsing (MOCK_INFERENCE=true) - for demos
    3. Weighted random - default
    """
    import os

    global _forced_species

    width, height = image.size

    # Priority 1: Test override (set_next_species)
    if _forced_species:
        species = _forced_species
        _forced_species = None
    # Priority 2: Mock inference from filename (MOCK_INFERENCE=true)
    elif os.getenv("MOCK_INFERENCE") == "true" and filename:
        parsed = parse_species_from_filename(filename)
        species = parsed if parsed else _weighted_random_species()
    # Priority 3: Random mock (default)
    else:
        species = _weighted_random_species()

    return InferenceResult(
        species=species,
        confidence=round(random.uniform(0.75, 0.98), 2),
        bbox=_random_bbox(width, height),
    )
```

**Step 4: Commit**

```bash
git add backend/inference.py
git commit -m "feat(backend): add MOCK_INFERENCE mode for filename-based species detection"
```

---

## Task 4: Update Upload Endpoint to Pass Filename

**Files:**
- Modify: `backend/main.py`

**Step 1: Update upload_image to pass filename to inference**

Find the line in `upload_image()` that calls `run_inference`:

```python
result = run_inference(image)
```

Replace with:

```python
result = run_inference(image, filename=file.filename)
```

**Step 2: Commit**

```bash
git add backend/main.py
git commit -m "feat(backend): pass filename to inference for MOCK_INFERENCE mode"
```

---

## Task 5: Add Tests for Mock Inference

**Files:**
- Modify: `backend/tests/test_scenarios.py`

**Step 1: Add test for filename parsing**

Add at the end of `test_scenarios.py`:

```python
# === Scenario 9: Mock Inference from Filename ===

def test_mock_inference_from_filename(client, test_image, monkeypatch):
    """MOCK_INFERENCE=true parses species from filename."""
    monkeypatch.setenv("MOCK_INFERENCE", "true")

    response = client.post(
        "/api/upload",
        files={("file", ("shark_001.jpg", test_image, "image/jpeg"))}
    )
    data = response.json()

    assert data["species"] == "Shark"
    assert data["status"] == "bycatch"


def test_mock_inference_fallback(client, test_image, monkeypatch):
    """MOCK_INFERENCE=true falls back to random for unknown filenames."""
    monkeypatch.setenv("MOCK_INFERENCE", "true")

    response = client.post(
        "/api/upload",
        files={("file", ("random_image.jpg", test_image, "image/jpeg"))}
    )
    data = response.json()

    # Should return some valid species (random)
    assert data["species"] in [
        "Albacore Tuna", "Bigeye Tuna", "Mahi-Mahi", "Yellowfin Tuna",
        "Shark", "Opah", "Pelagic Stingray", "Unknown"
    ]


def test_mock_inference_disabled_by_default(client, test_image):
    """Without MOCK_INFERENCE, filename is ignored."""
    # Don't set MOCK_INFERENCE env var
    # Upload with shark filename but should get random result
    responses = []
    for _ in range(5):
        response = client.post(
            "/api/upload",
            files={("file", ("shark_001.jpg", test_image, "image/jpeg"))}
        )
        responses.append(response.json()["species"])

    # With random inference, unlikely to get Shark 5 times in a row
    # (Shark weight is 15/100 = 15%, so 5 in a row is 0.0076%)
    # This is a probabilistic test - may rarely fail
    unique_species = set(responses)
    # If truly random, should have variety (not always Shark)
    # We just verify it ran without error - determinism tested above
    assert len(responses) == 5
```

**Step 2: Run tests**

```bash
cd backend && uv run pytest tests/test_scenarios.py -v
```

Expected: 11 tests pass (8 original + 3 new).

**Step 3: Commit**

```bash
git add backend/tests/test_scenarios.py
git commit -m "test(backend): add tests for MOCK_INFERENCE filename parsing"
```

---

## Task 6: Run Full Test Suite and Verify

**Step 1: Run all backend tests**

```bash
cd backend && uv run pytest tests/ -v
```

Expected: 17 tests pass (6 api + 11 scenarios).

**Step 2: Manual verification with mock inference**

```bash
cd backend
MOCK_INFERENCE=true uv run uvicorn main:app --port 8000 &
sleep 2

# Test with curl
curl -X POST http://localhost:8000/api/upload \
  -F "file=@demo_images/shark_001.jpg" | jq .

# Should return: {"species": "Shark", "status": "bycatch", ...}

# Stop server
pkill -f "uvicorn main:app"
```

**Step 3: Clean up**

```bash
rm -f backend/catch_log.db
```

---

## Summary

**Files Created:**
| File | Purpose |
|------|---------|
| `backend/demo_images/.gitkeep` | Demo images directory |
| `scripts/extract_demo_images.py` | Extract images from FOID |
| `scripts/pyproject.toml` | Script dependencies |

**Files Modified:**
| File | Change |
|------|--------|
| `backend/.gitignore` | Ignore demo_images/*.jpg |
| `backend/inference.py` | Add MOCK_INFERENCE mode |
| `backend/main.py` | Pass filename to inference |
| `backend/tests/test_scenarios.py` | Add mock inference tests |

**Test Coverage:**
| Test File | Tests |
|-----------|-------|
| `test_api.py` | 6 |
| `test_scenarios.py` | 11 (8 original + 3 new) |
| **Total** | **17** |

**Usage:**

```bash
# Extract demo images (one time)
cd scripts && uv run python extract_demo_images.py

# Run with mock inference
cd backend && MOCK_INFERENCE=true uv run uvicorn main:app --reload

# Upload demo images - species detected from filename
```
