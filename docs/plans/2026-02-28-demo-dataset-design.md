# Demo Dataset & Mock Inference Design

## Overview

Create a curated demo dataset from FOID v0.12 and add `MOCK_INFERENCE` mode to the backend for deterministic UI testing before the fine-tuned model is ready.

## Goals

1. **Demo Dataset**: Extract 2-3 representative images per species for manual UI testing
2. **Mock Inference**: Enable filename-based species detection for predictable demo flows
3. **Zero Impact**: Production code unchanged when `MOCK_INFERENCE=false` (default)

---

## Part 1: Demo Dataset

### Source
- FOID v0.12 dataset at `data/foid_v012/`
- Labels: `labels/foid_labels_bbox_v012.csv`
- Images: `images/{img_id}.jpg` (1280×720)

### Target Species (8 total)

| Species | Dataset Label | Status | Available | Extract |
|---------|---------------|--------|-----------|---------|
| Albacore Tuna | Albacore | legal | 33,943 | 3 |
| Bigeye Tuna | Bigeye tuna | legal | 2,772 | 2 |
| Mahi-Mahi | Mahi mahi | legal | 1,112 | 2 |
| Yellowfin Tuna | Yellowfin tuna | legal | 6,693 | 3 |
| Shark | Shark | bycatch | 623 | 3 |
| Opah | Opah | bycatch | 1,606 | 2 |
| Pelagic Stingray | Pelagic stingray | protected | 40 | 3 |
| Unknown | Unknown | unknown | 2,702 | 2 |

**Total: ~20 images**

### Output Structure

```
backend/demo_images/
├── albacore-tuna_001.jpg
├── albacore-tuna_002.jpg
├── albacore-tuna_003.jpg
├── bigeye-tuna_001.jpg
├── bigeye-tuna_002.jpg
├── mahi-mahi_001.jpg
├── mahi-mahi_002.jpg
├── yellowfin-tuna_001.jpg
├── yellowfin-tuna_002.jpg
├── yellowfin-tuna_003.jpg
├── shark_001.jpg
├── shark_002.jpg
├── shark_003.jpg
├── opah_001.jpg
├── opah_002.jpg
├── pelagic-stingray_001.jpg
├── pelagic-stingray_002.jpg
├── pelagic-stingray_003.jpg
├── unknown_001.jpg
└── unknown_002.jpg
```

### Filename Convention

Pattern: `{species-slug}_{number}.jpg`

| Species | Slug |
|---------|------|
| Albacore Tuna | `albacore-tuna` |
| Bigeye Tuna | `bigeye-tuna` |
| Mahi-Mahi | `mahi-mahi` |
| Yellowfin Tuna | `yellowfin-tuna` |
| Shark | `shark` |
| Opah | `opah` |
| Pelagic Stingray | `pelagic-stingray` |
| Unknown | `unknown` |

### Selection Criteria

The extraction script will:
1. Filter images where fish bbox is prominent (area > 5% of image)
2. Prefer images with single fish (cleaner demo)
3. Randomly sample from qualifying images
4. Copy and rename to target directory

---

## Part 2: Mock Inference Mode

### Environment Variable

```bash
MOCK_INFERENCE=true   # Parse species from filename
MOCK_INFERENCE=false  # Use real model (default)
```

### Filename Parsing Logic

```python
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

def parse_species_from_filename(filename: str) -> str | None:
    """Extract species from filename like 'shark_001.jpg' -> 'Shark'."""
    stem = Path(filename).stem  # 'shark_001'
    # Remove trailing _NNN
    slug = re.sub(r'_\d+$', '', stem)  # 'shark'
    return FILENAME_TO_SPECIES.get(slug)
```

### Integration with run_inference()

```python
def run_inference(image: Image.Image, filename: str | None = None) -> InferenceResult:
    global _forced_species

    # Priority 1: Test override (set_next_species)
    if _forced_species:
        species = _forced_species
        _forced_species = None
    # Priority 2: Mock inference from filename
    elif os.getenv("MOCK_INFERENCE") == "true" and filename:
        species = parse_species_from_filename(filename) or _weighted_random_species()
    # Priority 3: Random mock (default)
    else:
        species = _weighted_random_species()

    return InferenceResult(
        species=species,
        confidence=round(random.uniform(0.75, 0.98), 2),
        bbox=_random_bbox(width, height),
    )
```

### API Change

The `/api/upload` endpoint passes the filename to inference:

```python
@app.post("/api/upload")
async def upload_image(file: UploadFile):
    # ... existing code ...
    result = run_inference(image, filename=file.filename)
    # ... rest unchanged ...
```

---

## Part 3: Extraction Script

### Location
`scripts/extract_demo_images.py`

### Dependencies
- pandas (read CSV)
- shutil (copy files)
- pathlib (path handling)

### Algorithm

```
1. Load labels CSV
2. Filter to fish-only (exclude HUMAN, NoF)
3. For each target species:
   a. Filter to images containing that species
   b. Calculate bbox area as % of image
   c. Filter to images where bbox area > 5%
   d. Prefer images with single fish bbox
   e. Randomly sample N images
   f. Copy to demo_images/ with renamed filename
4. Print summary
```

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/extract_demo_images.py` | Create | Extract demo images from FOID |
| `backend/demo_images/` | Create | Directory with ~20 demo images |
| `backend/inference.py` | Modify | Add MOCK_INFERENCE mode |
| `backend/main.py` | Modify | Pass filename to inference |

---

## Testing

### 1. Verify extraction script

```bash
cd scripts && uv run python extract_demo_images.py
ls -la ../backend/demo_images/
```

Expected: ~20 images with correct naming.

### 2. Verify mock inference

```bash
cd backend
MOCK_INFERENCE=true uv run uvicorn main:app --reload
```

Upload `shark_001.jpg` → should return "Shark".
Upload `pelagic-stingray_001.jpg` → should return "Pelagic Stingray".

### 3. Verify default behavior unchanged

```bash
cd backend
uv run uvicorn main:app --reload
```

Upload any image → should return random species (existing behavior).

---

## Demo Flow Example

1. Start server with mock inference:
   ```bash
   MOCK_INFERENCE=true uv run uvicorn main:app --reload
   ```

2. Open UI at `http://localhost:3000`

3. Upload demo images in sequence:
   - `albacore-tuna_001.jpg` → Legal catch, counter +1
   - `albacore-tuna_002.jpg` → Legal catch, counter +2
   - `shark_001.jpg` → Bycatch alert, ACTION_REQUIRED
   - Click Release → Back to COMPLIANT
   - `pelagic-stingray_001.jpg` → Critical alert, ACTION_REQUIRED
   - Click Release → Back to COMPLIANT

4. Demo complete - all flows tested deterministically.
