# Critical Fixes Design

**Date:** 2026-02-28
**Status:** Approved
**Scope:** Fine-tuning notebook + Backend inference integration

---

## Overview

Two-part fix to resolve critical blockers before training and demo:
1. **Part A:** Fix species code collisions and status errors in fine-tuning notebook
2. **Part B:** Add PaliGemma output parsing to backend with priority-based detection selection

---

## Part A: Fine-tuning Notebook Fixes

### File
`catchlog_finetune.ipynb` (cell-5)

### Problem 1: BILL Code Collision
6 species with different regulatory statuses map to the same output code `BILL`:

```python
# CURRENT (broken)
"Swordfish":           {"name": "BILL",   "status": "legal_regulated"},
"Striped marlin":      {"name": "BILL",   "status": "protected"},
"Blue marlin":         {"name": "BILL",   "status": "protected"},
"Black marlin":        {"name": "BILL",   "status": "protected"},
"Shortbill spearfish": {"name": "BILL",   "status": "legal_regulated"},
"Indo Pacific sailfish": {"name": "BILL", "status": "protected"},
```

### Problem 2: Pelagic Stingray Status
Protected species substitute incorrectly marked as bycatch:

```python
# CURRENT (broken)
"Pelagic stingray":    {"name": "PLS",    "status": "bycatch"},
```

### Solution

Replace `TARGET_SPECIES` dict with unique codes and correct statuses:

```python
TARGET_SPECIES = {
    # Legal species
    "Albacore":               {"name": "ALB",    "status": "legal"},
    "Yellowfin tuna":         {"name": "YFT",    "status": "legal"},
    "Bigeye tuna":            {"name": "BET",    "status": "legal"},
    "Skipjack tuna":          {"name": "SKJ",    "status": "legal"},
    "Mahi mahi":              {"name": "DOL",    "status": "legal"},
    "Swordfish":              {"name": "SWO",    "status": "legal"},
    "Shortbill spearfish":    {"name": "SSF",    "status": "legal"},
    "Oilfish":                {"name": "OIL",    "status": "legal"},
    "Wahoo":                  {"name": "WAH",    "status": "legal"},
    "Long snouted lancetfish": {"name": "LAF",   "status": "legal"},
    "Great barracuda":        {"name": "GBA",    "status": "legal"},
    "Sickle pomfret":         {"name": "SIP",    "status": "legal"},
    "Pomfret":                {"name": "POM",    "status": "legal"},
    "Rainbow runner":         {"name": "RRU",    "status": "legal"},
    "Snake mackerel":         {"name": "SNM",    "status": "legal"},
    "Roudie scolar":          {"name": "RSC",    "status": "legal"},

    # Bycatch species (release required)
    "Shark":                  {"name": "SHARK",  "status": "bycatch"},
    "Thresher shark":         {"name": "THR",    "status": "bycatch"},
    "Opah":                   {"name": "OPA",    "status": "bycatch"},
    "Mola mola":              {"name": "MOL",    "status": "bycatch"},

    # Protected species (immediate release required)
    "Striped marlin":         {"name": "STM",    "status": "protected"},
    "Blue marlin":            {"name": "BUM",    "status": "protected"},
    "Black marlin":           {"name": "BLM",    "status": "protected"},
    "Indo Pacific sailfish":  {"name": "SAI",    "status": "protected"},
    "Pelagic stingray":       {"name": "PLS",    "status": "protected"},

    # Unknown / Other
    "Unknown":                {"name": "UNK",    "status": "unknown"},

    # Ignore (not fish)
    "No fish":                {"name": "NoF",    "status": "ignore"},
}
```

### Changes Summary

| Species | Old Code | New Code | Old Status | New Status |
|---------|----------|----------|------------|------------|
| Swordfish | BILL | SWO | legal_regulated | legal |
| Striped marlin | BILL | STM | protected | protected |
| Blue marlin | BILL | BUM | protected | protected |
| Black marlin | BILL | BLM | protected | protected |
| Shortbill spearfish | BILL | SSF | legal_regulated | legal |
| Indo Pacific sailfish | BILL | SAI | protected | protected |
| Pelagic stingray | PLS | PLS | bycatch | **protected** |
| Opah | LAG | OPA | legal | **bycatch** |

### Estimated Time
10 minutes

---

## Part B: Backend Inference Integration

### Files
- `backend/inference.py` (modify)

### Problem
Model outputs PaliGemma format, backend expects `InferenceResult`:

| Model Output | Backend Expects |
|--------------|-----------------|
| `<loc0340><loc0156><loc0782><loc0534> ALB` | `InferenceResult(species="Albacore Tuna", bbox=[156, 340, 534, 782], confidence=0.9)` |
| Normalized coords (0-1023) | Pixel coordinates |
| Species codes | Display names |
| Multiple detections | Single most-critical detection |

### Solution

#### 1. Code-to-Species Mapping

```python
CODE_TO_SPECIES = {
    # Legal
    "ALB": "Albacore Tuna",
    "YFT": "Yellowfin Tuna",
    "BET": "Bigeye Tuna",
    "SKJ": "Skipjack Tuna",
    "DOL": "Mahi-Mahi",
    "SWO": "Swordfish",
    "SSF": "Shortbill Spearfish",
    "OIL": "Oilfish",
    "WAH": "Wahoo",
    "LAF": "Long Snouted Lancetfish",
    "GBA": "Great Barracuda",
    "SIP": "Sickle Pomfret",
    "POM": "Pomfret",
    "RRU": "Rainbow Runner",
    "SNM": "Snake Mackerel",
    "RSC": "Roudie Scolar",
    # Bycatch
    "SHARK": "Shark",
    "THR": "Thresher Shark",
    "OPA": "Opah",
    "MOL": "Mola Mola",
    # Protected
    "STM": "Striped Marlin",
    "BUM": "Blue Marlin",
    "BLM": "Black Marlin",
    "SAI": "Indo Pacific Sailfish",
    "PLS": "Pelagic Stingray",
    # Other
    "UNK": "Unknown",
    "NoF": "No Fish",
}

def code_to_species(code: str) -> str:
    """Map species code to display name with Unknown fallback."""
    return CODE_TO_SPECIES.get(code.strip(), "Unknown")
```

#### 2. PaliGemma Output Parser

```python
import re

def parse_paligemma_output(raw_output: str, img_w: int, img_h: int) -> list[InferenceResult]:
    """
    Parse PaliGemma detection output to InferenceResult objects.

    Input format: '<loc0340><loc0156><loc0782><loc0534> ALB ; <loc...> BET'
    Loc order: y1, x1, y2, x2 (normalized 0-1023)
    """
    pattern = r'<loc(\d{4})><loc(\d{4})><loc(\d{4})><loc(\d{4})>\s*([^<;]+)'
    matches = re.findall(pattern, raw_output)

    results = []
    for y1, x1, y2, x2, code in matches:
        # Convert normalized coords to pixels
        bbox = [
            int(int(x1) / 1023 * img_w),  # x1
            int(int(y1) / 1023 * img_h),  # y1
            int(int(x2) / 1023 * img_w),  # x2
            int(int(y2) / 1023 * img_h),  # y2
        ]

        species = code_to_species(code)

        results.append(InferenceResult(
            species=species,
            confidence=0.90,  # PaliGemma doesn't output confidence
            bbox=bbox,
        ))

    return results
```

#### 3. Priority-Based Selection

```python
# Status priority: protected > bycatch > unknown > legal
STATUS_PRIORITY = {
    "protected": 0,
    "bycatch": 1,
    "unknown": 2,
    "legal": 3,
    "ignore": 4,
}

def get_species_status(species_name: str) -> str:
    """Look up regulatory status for a species."""
    from database import get_species_by_name
    info = get_species_by_name(species_name)
    if not info:
        return "unknown"
    status_code = info["status"]
    return {0: "legal", 1: "bycatch", 2: "protected", 3: "unknown"}.get(status_code, "unknown")

def pick_most_critical(detections: list[InferenceResult]) -> InferenceResult | None:
    """Return detection with highest regulatory priority."""
    if not detections:
        return None
    return min(detections, key=lambda d: STATUS_PRIORITY.get(get_species_status(d.species), 99))
```

#### 4. Updated run_inference Function

```python
def run_inference(image: Image.Image, filename: str | None = None) -> InferenceResult:
    """
    Run inference on an image and return the most critical detection.
    """
    import os

    width, height = image.size

    # Check for mock mode (existing logic)
    if os.getenv("MOCK_INFERENCE") == "true":
        # ... existing mock logic ...
        pass

    # Real inference with loaded model
    if _model and _model != "mock":
        raw_output = _run_paligemma(image)
        detections = parse_paligemma_output(raw_output, width, height)
        result = pick_most_critical(detections)
        if result:
            return result
        # Fallback if no detections
        return InferenceResult(species="Unknown", confidence=0.5, bbox=[0, 0, 100, 100])

    # Default mock fallback
    return InferenceResult(
        species=_weighted_random_species(),
        confidence=round(random.uniform(0.75, 0.98), 2),
        bbox=_random_bbox(width, height),
    )
```

### Data Flow

```
Image Upload
    │
    ▼
run_inference(image)
    │
    ▼
_run_paligemma(image)
    │
    ▼
"<loc0340><loc0156><loc0782><loc0534> ALB ; <loc0100><loc0200><loc0400><loc0500> PLS"
    │
    ▼
parse_paligemma_output(raw, w, h)
    │
    ▼
[InferenceResult(Albacore Tuna, ...), InferenceResult(Pelagic Stingray, ...)]
    │
    ▼
pick_most_critical(detections)
    │
    ▼
InferenceResult(Pelagic Stingray, ...)  ← Protected wins over Legal
    │
    ▼
Agent processes → Alert triggered
```

### Estimated Time
30 minutes

---

## Scope Decisions

### In Scope
- Fix species code collisions (BILL → unique codes)
- Fix Pelagic Stingray status (bycatch → protected)
- Add PaliGemma output parser
- Add code-to-species mapping
- Add priority-based detection selection

### Out of Scope (Decided)
- Frontend polling (not needed for upload-based demo)
- Autonomous video loop (not needed for upload-based demo)
- Multi-detection UI display (single detection sufficient)
- Real-time ElevenLabs API (pre-generated audio sufficient)

---

## Testing Checklist

### Part A (Notebook)
- [ ] All species have unique codes
- [ ] No duplicate codes with different statuses
- [ ] Pelagic Stingray status is "protected"
- [ ] Opah status is "bycatch"
- [ ] Training runs without errors

### Part B (Backend)
- [ ] `parse_paligemma_output` correctly extracts all detections
- [ ] Bbox coordinates scale correctly to image size
- [ ] Code mapping returns correct display names
- [ ] Unknown codes fall back to "Unknown"
- [ ] `pick_most_critical` returns protected over bycatch over legal
- [ ] Integration with existing `process_image` flow works

---

## Implementation Order

1. **Part A first** - Fix notebook before training
2. **Train model** - Run fine-tuning with fixed species
3. **Part B** - Add backend parsing while model trains (can parallelize)
4. **Integration test** - Upload test images through full pipeline

---

*Design approved: 2026-02-28*
