# Fine-Tuning Notebook Review

**Reviewed:** `catchlog_finetune.ipynb`
**Date:** 2026-02-28

---

## What's Good

| Aspect | Implementation | Notes |
|--------|---------------|-------|
| PaliGemma format | `<locYYYY><locXXXX>...` | Correct normalized coords (0-1023) |
| Balancing | 600 samples/species cap | Prevents Albacore (33k) from dominating |
| QLoRA | 4-bit quantization, LoRA rank 8 | Memory efficient |
| Multi-object | All bboxes per image in one suffix | Correct approach |
| Train/Val split | 90/10 | Standard |

---

## Issues Found

### 1. Species Code Collision (CRITICAL)

Multiple species with **different regulatory statuses** map to the same code:

```python
"Swordfish":              {"name": "BILL",   "status": "legal_regulated"},
"Striped marlin":         {"name": "BILL",   "status": "protected"},
"Blue marlin":            {"name": "BILL",   "status": "protected"},
```

**Problem:** Model outputs `BILL` → backend can't tell if it's legal Swordfish or protected Blue Marlin.

**Fix:** Use distinct codes or full species names:
```python
"Swordfish":              {"name": "SWO",    "status": "legal"},
"Striped marlin":         {"name": "STM",    "status": "protected"},
"Blue marlin":            {"name": "BUM",    "status": "protected"},
```

---

### 2. Rare Class Problem (HIGH)

| Species | Samples | Cap | Result |
|---------|---------|-----|--------|
| Pelagic stingray | 40 | 600 | Only 40 used |
| Mola mola | 6 | 600 | Only 6 used |
| Thresher shark | 1 | 600 | Only 1 used |

**Problem:** Model will rarely see protected species during training → poor recall on the most critical class.

**Fix options:**
- A) Data augmentation (flip, rotate, brightness) to 5x the rare samples
- B) Oversample rare classes (repeat them in training)
- C) Class-weighted loss function
- D) Focus POC on Pelagic stingray only (40 samples > 6)

---

### 3. Human/NoF in Training Data (MEDIUM)

```python
"No fish":                {"name": "NoF",    "status": "none"},
"Human":                  {"name": "HUMAN",  "status": "none"},
```

**Question:** Is this intentional?
- If YES: Model learns to detect humans/empty frames (useful for filtering)
- If NO: Remove from TARGET_SPECIES to focus on fish

**Recommendation:** Keep NoF (teaches "nothing here"), remove HUMAN (104k samples will dominate even with cap).

---

### 4. No Stratified Split (MEDIUM)

```python
random.shuffle(all_entries)
split_idx = int(len(all_entries) * (1 - VAL_SPLIT))
```

**Problem:** Random split may put all 6 Mola mola in train, none in val.

**Fix:**
```python
from sklearn.model_selection import train_test_split

# Stratify by primary species
train_entries, val_entries = train_test_split(
    all_entries,
    test_size=VAL_SPLIT,
    stratify=[e['species'][0] for e in all_entries],
    random_state=42
)
```

---

### 5. Status Mismatch with Backend (MEDIUM)

| Species | Notebook Status | Backend Design | Recommendation |
|---------|-----------------|----------------|----------------|
| Pelagic stingray | bycatch | protected | **Use protected** |
| Opah | legal | bycatch | Use legal (it's edible) |
| Striped marlin | protected | bycatch | Use protected |
| Bigeye tuna | legal_quota | legal | Use legal |

**Fix:** Align on 4 statuses: `legal`, `bycatch`, `protected`, `unknown`

---

### 6. Data Path Issue (LOW)

```python
IMAGES_DIR = "data/images"
```

**Problem:** Relative path assumes data is copied to notebook directory.

**Current data location:**
```
/Users/misran/Documents/misu/instalily-ai-hackathon/catchlog/data/foid_v012/images/
```

**Fix:** Either symlink or use absolute path.

---

### 7. No Validation Metrics Beyond Species Match (LOW)

```python
match = bool(expected & predicted)
```

**Problem:** Only checks if any species matches. Doesn't measure:
- Bbox accuracy (IoU)
- Precision/Recall per class
- False positive rate

**For hackathon:** Acceptable. Species match is the core demo.

**For production:** Add mAP calculation.

---

## Recommended Changes

### Priority 1: Fix Species Code Collision

```python
TARGET_SPECIES = {
    # Legal - use specific codes
    "Albacore":           {"name": "ALB",   "status": "legal"},
    "Yellowfin tuna":     {"name": "YFT",   "status": "legal"},
    "Bigeye tuna":        {"name": "BET",   "status": "legal"},
    "Skipjack tuna":      {"name": "SKJ",   "status": "legal"},
    "Mahi mahi":          {"name": "DOL",   "status": "legal"},
    "Swordfish":          {"name": "SWO",   "status": "legal"},

    # Bycatch - release required
    "Shark":              {"name": "SHK",   "status": "bycatch"},
    "Opah":               {"name": "OPA",   "status": "bycatch"},
    "Oilfish":            {"name": "OIL",   "status": "bycatch"},

    # Protected - immediate release
    "Pelagic stingray":   {"name": "PLS",   "status": "protected"},
    "Blue marlin":        {"name": "BUM",   "status": "protected"},
    "Striped marlin":     {"name": "STM",   "status": "protected"},

    # Unknown
    "Unknown":            {"name": "UNK",   "status": "unknown"},

    # Ignore (keep for filtering, but don't count as fish)
    "No fish":            {"name": "NOF",   "status": "ignore"},
}
```

### Priority 2: Augment Protected Species

```python
# After building species_entries, augment rare classes
from PIL import ImageOps, ImageEnhance

def augment_entry(entry, aug_type):
    """Create augmented version of an entry."""
    img = Image.open(entry['image'])

    if aug_type == 'flip_h':
        img = ImageOps.mirror(img)
        # Also flip bbox x coordinates
    elif aug_type == 'flip_v':
        img = ImageOps.flip(img)
    elif aug_type == 'bright':
        img = ImageEnhance.Brightness(img).enhance(1.3)
    elif aug_type == 'dark':
        img = ImageEnhance.Brightness(img).enhance(0.7)

    # Save augmented image
    aug_path = entry['image'].replace('.jpg', f'_{aug_type}.jpg')
    img.save(aug_path)

    return {**entry, 'image': aug_path}

# Augment species with < 100 samples
MIN_SAMPLES = 100
for species, entries in species_entries.items():
    if len(entries) < MIN_SAMPLES:
        augmented = []
        for entry in entries:
            for aug in ['flip_h', 'bright', 'dark']:
                augmented.append(augment_entry(entry, aug))
        species_entries[species].extend(augmented)
```

### Priority 3: Remove Human from Training

```python
# Remove Human - too many samples, not a fish
del TARGET_SPECIES["Human"]
```

---

## Summary

| Issue | Severity | Effort | Recommendation |
|-------|----------|--------|----------------|
| Species code collision | CRITICAL | 10 min | Fix before training |
| Rare class problem | HIGH | 30 min | Augment protected species |
| Human in training | MEDIUM | 1 min | Remove from TARGET_SPECIES |
| No stratified split | MEDIUM | 5 min | Use sklearn stratify |
| Status mismatch | MEDIUM | 5 min | Sync with backend |
| Data path | LOW | 1 min | Use absolute path |

**Total fix time:** ~1 hour

**Without fixes:** Model will work but can't distinguish protected Marlin from legal Swordfish.
