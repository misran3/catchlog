# CatchLog Data Exploration Findings

**Date:** 2026-02-28
**Dataset:** FOID v0.12 (Fish Object Identification Dataset)

---

## Executive Summary

The FOID dataset provides **34,987 images** with **52,737 fish bounding boxes** across **26 species**. All required regulatory statuses (legal, bycatch, protected, unknown) are represented, but with significant class imbalance. Key finding: **Sea Turtle is NOT in the dataset** - recommend using **Pelagic Stingray** (40 samples) or **Mola Mola** (6 samples) as the protected species instead.

---

## Dataset Overview

| Metric | Value |
|--------|-------|
| Total images | 34,987 |
| Total bounding boxes | 159,119 |
| Fish bounding boxes | 52,737 |
| Human bounding boxes | 104,503 |
| "No fish" frames | 1,879 |
| Image resolution | 1280 × 720 |
| Fish species count | 26 |

---

## Species by Regulatory Status

### 🟢 LEGAL (Target Species) - 45,930 samples

| Species | Count | Notes |
|---------|-------|-------|
| Albacore | 33,943 | Primary target - abundant data |
| Yellowfin tuna | 6,693 | High-value target |
| Bigeye tuna | 2,772 | High-value target |
| Mahi mahi | 1,112 | Dolphinfish |
| Skipjack tuna | 693 | Common target |
| Wahoo | 468 | Optional addition |
| Swordfish | 247 | Often legal with permits |

### 🟡 BYCATCH (Release Required) - 4,059 samples

| Species | Count | Notes |
|---------|-------|-------|
| Opah | 1,606 | Moonfish - distinctive |
| Oilfish | 778 | Incidental catch |
| Shark | 623 | Generic shark class |
| Striped marlin | 224 | Billfish |
| Blue marlin | 177 | Billfish |
| Others | 651 | Various billfish, lancetfish |

### 🔴 PROTECTED (Immediate Release) - 46 samples

| Species | Count | Notes |
|---------|-------|-------|
| Pelagic stingray | 40 | **Recommended for POC** |
| Mola mola | 6 | Ocean sunfish - distinctive but rare |

### ⚪ UNKNOWN - 2,702 samples

Species that couldn't be identified - good for edge case testing.

---

## Recommended Species for POC

### Tier 1: Minimum Viable (5 species)

Use this for fastest development and demo:

```
🟢 Albacore Tuna      - legal     - 33,943 samples
🟢 Yellowfin Tuna     - legal     -  6,693 samples
🟡 Shark              - bycatch   -    623 samples
🔴 Pelagic Stingray   - protected -     40 samples
⚪ Unknown            - unknown   -  2,702 samples
```

### Tier 2: Full POC (10 species)

Use this for comprehensive demo:

```
🟢 Albacore Tuna      - legal     - 33,943 samples
🟢 Yellowfin Tuna     - legal     -  6,693 samples
🟢 Bigeye Tuna        - legal     -  2,772 samples
🟢 Mahi-Mahi          - legal     -  1,112 samples
🟢 Skipjack Tuna      - legal     -    693 samples
🟡 Shark              - bycatch   -    623 samples
🟡 Opah               - bycatch   -  1,606 samples
🟡 Blue Marlin        - bycatch   -    177 samples
🔴 Pelagic Stingray   - protected -     40 samples
⚪ Unknown            - unknown   -  2,702 samples
```

---

## Fine-Tuning Data Recommendations

### For 6-Hour Hackathon (Option C - Minimal)

**~840 samples total** - fastest to train:

| Species | Samples | Status |
|---------|---------|--------|
| Albacore | 200 | legal |
| Yellowfin tuna | 200 | legal |
| Shark | 200 | bycatch |
| Pelagic stingray | 40 (all) | protected |
| Unknown | 200 | unknown |

**Training time estimate:** ~30-60 min on consumer GPU

### For Quality POC (Option B - Weighted)

**~5,110 samples total** - better accuracy:

| Species | Samples | Status |
|---------|---------|--------|
| Albacore | 800 | legal |
| Yellowfin tuna | 800 | legal |
| Bigeye tuna | 800 | legal |
| Mahi mahi | 800 | legal |
| Skipjack tuna | 693 | legal |
| Shark | 400 | bycatch |
| Opah | 400 | bycatch |
| Blue marlin | 177 | bycatch |
| Pelagic stingray | 40 (all) | protected |
| Unknown | 200 | unknown |

**Training time estimate:** 2-4 hours on consumer GPU

---

## Backend Changes Required

### 1. Update Species Table

**Current design (6 species):**
```python
SPECIES_DATA = [
    (1, "Albacore Tuna", 0),
    (2, "Bigeye Tuna", 0),
    (3, "Mahi-Mahi", 0),
    (4, "Blue Shark", 1),
    (5, "Sea Turtle", 2),  # ❌ NOT IN DATASET
    (6, "Unknown", 3),
]
```

**Recommended (matches dataset):**
```python
SPECIES_DATA = [
    # Legal (status=0)
    (1, "Albacore Tuna", 0),
    (2, "Yellowfin Tuna", 0),
    (3, "Bigeye Tuna", 0),
    (4, "Mahi-Mahi", 0),
    (5, "Skipjack Tuna", 0),
    # Bycatch (status=1)
    (6, "Shark", 1),
    (7, "Opah", 1),
    (8, "Blue Marlin", 1),
    # Protected (status=2)
    (9, "Pelagic Stingray", 2),
    # Unknown (status=3)
    (10, "Unknown", 3),
]
```

### 2. Update Inference Module

**Add species name mapping:**
```python
# Map model output labels to display names
LABEL_TO_DISPLAY = {
    "Albacore": "Albacore Tuna",
    "Yellowfin tuna": "Yellowfin Tuna",
    "Bigeye tuna": "Bigeye Tuna",
    "Mahi mahi": "Mahi-Mahi",
    "Skipjack tuna": "Skipjack Tuna",
    "Shark": "Shark",
    "Opah": "Opah",
    "Blue marlin": "Blue Marlin",
    "Pelagic stingray": "Pelagic Stingray",
    "Unknown": "Unknown",
}
```

### 3. Fix BBox Format

**Dataset format:** `[x_min, x_max, y_min, y_max]`
**Backend expects:** `[x1, y1, x2, y2]`

```python
# Conversion needed in inference.py
def convert_bbox(dataset_bbox):
    x_min, x_max, y_min, y_max = dataset_bbox
    return [x_min, y_min, x_max, y_max]
```

---

## UI Changes Required

### 1. Update CatchCounter Species List

```typescript
// frontend/components/CatchCounter.tsx
const SPECIES_STATUS: Record<string, Status> = {
  "Albacore Tuna": "legal",
  "Yellowfin Tuna": "legal",
  "Bigeye Tuna": "legal",
  "Mahi-Mahi": "legal",
  "Skipjack Tuna": "legal",
  "Shark": "bycatch",
  "Opah": "bycatch",
  "Blue Marlin": "bycatch",
  "Pelagic Stingray": "protected",  // Was Sea Turtle
  "Unknown": "unknown",
};
```

### 2. Update Alert Messages

```typescript
// For protected species alert
if (status === "protected") {
  return `PROTECTED: ${species} — Immediate release required`;
}
```

### 3. Add Species Icons (Optional Enhancement)

Consider adding species-specific icons or silhouettes for quick visual identification in the counter.

---

## Data Quality Notes

### Image Characteristics
- **Resolution:** 1280×720 (HD)
- **Source:** Fishing vessel deck cameras
- **Challenges:** Motion blur, varying lighting, occlusion by crew
- **Multi-object:** Average 4.5 bboxes per image

### Bounding Box Statistics
- **Median size:** 164×123 pixels (~2.2% of image)
- **Range:** 9×6 to 833×577 pixels
- **Aspect ratio:** Median ~1.3:1 (slightly wider than tall)

### Class Imbalance
- **Ratio:** 33,943:1 (Albacore vs Thresher shark)
- **Mitigation:** Use balanced sampling for fine-tuning
- **Protected species:** Only 46 total samples - consider data augmentation

---

## Files Generated

| File | Purpose |
|------|---------|
| `scripts/analyze_dataset.py` | Basic dataset statistics |
| `scripts/visualize_dataset.py` | Distribution charts |
| `scripts/regulatory_analysis.py` | Species by status |
| `scripts/poc_species_config.json` | Species config for backend |
| `scripts/species_mapping.json` | Label mapping |
| `scripts/output/*.png` | Visualization outputs |

---

## Next Steps

1. **Share `poc_species_config.json` with teammate** for fine-tuning
2. **Update backend `database.py`** with new species list
3. **Update frontend `CatchCounter.tsx`** with new species mapping
4. **Run fine-tuning** with Option C (840 samples) for hackathon speed
5. **Test with sample images** from each category before demo
