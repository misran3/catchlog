# Backend Integration Checklist

**After training completes, follow these steps to integrate the model.**

---

## Step 1: Download Model (~2 min)

```bash
# From local machine
scp hackathon@<VM_IP>:/home/hackathon/catchlog/output/catchlog-lora-adapter.zip ~/Downloads/

# Extract to backend
cd /path/to/catchlog/backend
mkdir -p models
unzip ~/Downloads/catchlog-lora-adapter.zip -d models/
```

Verify:
```bash
ls models/catchlog-lora-adapter/
# Should see: adapter_config.json, adapter_model.safetensors
```

---

## Step 2: Update inference.py (~15 min)

Replace `backend/inference.py` with this implementation:

```python
# backend/inference.py
"""Real PaliGemma inference with LoRA adapter."""

import os
import re
import torch
from dataclasses import dataclass
from PIL import Image

# ============================================================
# SPECIES MAPPING (matches train_full.py exactly)
# ============================================================

SPECIES_MAP = {
    # Legal (15 species)
    "ALB": {"name": "Albacore Tuna", "status": "legal"},
    "YFT": {"name": "Yellowfin Tuna", "status": "legal"},
    "BET": {"name": "Bigeye Tuna", "status": "legal"},
    "SKJ": {"name": "Skipjack Tuna", "status": "legal"},
    "DOL": {"name": "Mahi-Mahi", "status": "legal"},
    "SWO": {"name": "Swordfish", "status": "legal"},
    "WAH": {"name": "Wahoo", "status": "legal"},
    "SSF": {"name": "Shortbill Spearfish", "status": "legal"},
    "LAF": {"name": "Long Snouted Lancetfish", "status": "legal"},
    "BAR": {"name": "Great Barracuda", "status": "legal"},
    "SPF": {"name": "Sickle Pomfret", "status": "legal"},
    "POM": {"name": "Pomfret", "status": "legal"},
    "RRN": {"name": "Rainbow Runner", "status": "legal"},
    "SNM": {"name": "Snake Mackerel", "status": "legal"},
    "RSC": {"name": "Roudie Scolar", "status": "legal"},
    # Bycatch (5 species)
    "SHK": {"name": "Shark", "status": "bycatch"},
    "THR": {"name": "Thresher Shark", "status": "bycatch"},
    "OPA": {"name": "Opah", "status": "bycatch"},
    "OIL": {"name": "Oilfish", "status": "bycatch"},
    "MOL": {"name": "Mola Mola", "status": "bycatch"},
    # Protected (5 species)
    "PLS": {"name": "Pelagic Stingray", "status": "protected"},
    "STM": {"name": "Striped Marlin", "status": "protected"},
    "BUM": {"name": "Blue Marlin", "status": "protected"},
    "BKM": {"name": "Black Marlin", "status": "protected"},
    "SAI": {"name": "Indo Pacific Sailfish", "status": "protected"},
    # Other
    "UNK": {"name": "Unknown", "status": "unknown"},
    "NOF": {"name": "No Fish", "status": "ignore"},
}

STATUS_PRIORITY = {
    "protected": 1,
    "bycatch": 2,
    "unknown": 3,
    "legal": 4,
    "ignore": 5,
}

# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class InferenceResult:
    """Result from running inference on an image."""
    species: str
    confidence: float
    bbox: list[int]  # [x1, y1, x2, y2] in pixels


# ============================================================
# PARSING
# ============================================================

DETECTION_PATTERN = r'<loc(\d{4})><loc(\d{4})><loc(\d{4})><loc(\d{4})>\s*(\w+)'


def parse_detections(output_text: str, img_width: int, img_height: int) -> list[dict]:
    """Parse PaliGemma output into detection dicts."""
    detections = []

    for match in re.finditer(DETECTION_PATTERN, output_text):
        y1_norm, x1_norm, y2_norm, x2_norm, species_code = match.groups()

        # Skip ignored classes
        if species_code in ("NOF", "HUMAN"):
            continue

        # Convert normalized (0-1023) to pixel coordinates
        x1 = int(int(x1_norm) / 1023 * img_width)
        y1 = int(int(y1_norm) / 1023 * img_height)
        x2 = int(int(x2_norm) / 1023 * img_width)
        y2 = int(int(y2_norm) / 1023 * img_height)

        # Look up species info
        species_info = SPECIES_MAP.get(species_code, {"name": "Unknown", "status": "unknown"})

        detections.append({
            "species": species_info["name"],
            "status": species_info["status"],
            "bbox": [x1, y1, x2, y2],
            "confidence": 0.85,
        })

    return detections


def select_primary_detection(detections: list[dict]) -> dict | None:
    """Select most critical detection (protected > bycatch > unknown > legal)."""
    if not detections:
        return None
    return min(detections, key=lambda d: STATUS_PRIORITY.get(d["status"], 99))


# ============================================================
# MODEL LOADING
# ============================================================

_model = None
_processor = None
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
ADAPTER_PATH = "models/catchlog-lora-adapter"
BASE_MODEL_ID = "google/paligemma2-3b-pt-224"


def load_model(adapter_path: str = ADAPTER_PATH) -> None:
    """Load PaliGemma + LoRA adapter."""
    global _model, _processor

    # Check for mock mode
    if os.getenv("MOCK_INFERENCE") == "true":
        print("MOCK_INFERENCE=true - using mock inference")
        _model = "mock"
        return

    from transformers import PaliGemmaProcessor, PaliGemmaForConditionalGeneration
    from peft import PeftModel

    print(f"Loading processor from {BASE_MODEL_ID}...")
    _processor = PaliGemmaProcessor.from_pretrained(BASE_MODEL_ID)

    print(f"Loading base model to {DEVICE}...")
    _model = PaliGemmaForConditionalGeneration.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.float16,
        device_map=DEVICE,
    )

    print(f"Loading LoRA adapter from {adapter_path}...")
    _model = PeftModel.from_pretrained(_model, adapter_path)
    _model.eval()

    print("Model loaded!")


def is_model_loaded() -> bool:
    return _model is not None


def warmup_model() -> None:
    """Run dummy inference to JIT compile."""
    if _model == "mock":
        return
    print("Warming up model...")
    dummy = Image.new("RGB", (224, 224), color="blue")
    _run_raw_inference(dummy)
    print("Warmup complete!")


def _run_raw_inference(image: Image.Image) -> str:
    """Run inference, return raw model output."""
    inputs = _processor(
        text="<image>detect fish",
        images=image.convert("RGB"),
        return_tensors="pt"
    ).to(DEVICE, dtype=torch.float16)

    with torch.no_grad():
        output = _model.generate(**inputs, max_new_tokens=256)

    return _processor.decode(output[0], skip_special_tokens=False)


# ============================================================
# MOCK INFERENCE (for testing without model)
# ============================================================

import random

MOCK_SPECIES = [
    ("Albacore Tuna", "legal", 35),
    ("Yellowfin Tuna", "legal", 20),
    ("Shark", "bycatch", 15),
    ("Pelagic Stingray", "protected", 5),
    ("Unknown", "unknown", 2),
]


def _mock_inference(image: Image.Image, filename: str | None) -> InferenceResult:
    """Return mock result based on filename or random."""
    width, height = image.size

    # Check filename for species hint
    if filename:
        fname = filename.lower()
        if "stingray" in fname or "protected" in fname:
            species, status = "Pelagic Stingray", "protected"
        elif "shark" in fname:
            species, status = "Shark", "bycatch"
        elif "albacore" in fname:
            species, status = "Albacore Tuna", "legal"
        else:
            # Weighted random
            choices = [(s, st) for s, st, _ in MOCK_SPECIES]
            weights = [w for _, _, w in MOCK_SPECIES]
            species, status = random.choices(choices, weights=weights, k=1)[0]
    else:
        choices = [(s, st) for s, st, _ in MOCK_SPECIES]
        weights = [w for _, _, w in MOCK_SPECIES]
        species, status = random.choices(choices, weights=weights, k=1)[0]

    # Random bbox
    bw = random.randint(int(width * 0.2), int(width * 0.4))
    bh = random.randint(int(height * 0.2), int(height * 0.4))
    x1 = random.randint(0, width - bw)
    y1 = random.randint(0, height - bh)

    return InferenceResult(
        species=species,
        confidence=round(random.uniform(0.75, 0.95), 2),
        bbox=[x1, y1, x1 + bw, y1 + bh],
    )


# ============================================================
# PUBLIC INTERFACE
# ============================================================

def run_inference(image: Image.Image, filename: str | None = None) -> InferenceResult:
    """
    Run inference on an image, return primary detection.

    If MOCK_INFERENCE=true, returns mock results.
    Otherwise runs real PaliGemma inference.
    """
    if not is_model_loaded():
        raise RuntimeError("Model not loaded. Call load_model() first.")

    # Mock mode
    if _model == "mock":
        return _mock_inference(image, filename)

    # Real inference
    img_width, img_height = image.size
    raw_output = _run_raw_inference(image)
    detections = parse_detections(raw_output, img_width, img_height)
    primary = select_primary_detection(detections)

    if primary is None:
        return InferenceResult(
            species="Unknown",
            confidence=0.5,
            bbox=[0, 0, img_width, img_height],
        )

    return InferenceResult(
        species=primary["species"],
        confidence=primary["confidence"],
        bbox=primary["bbox"],
    )
```

---

## Step 3: Update database.py Species (~5 min)

Add missing species to `SPECIES_DATA`:

```python
SPECIES_DATA = [
    # Legal (status=0)
    (1, "Albacore Tuna", 0),
    (2, "Yellowfin Tuna", 0),
    (3, "Bigeye Tuna", 0),
    (4, "Skipjack Tuna", 0),
    (5, "Mahi-Mahi", 0),
    (6, "Swordfish", 0),
    (7, "Wahoo", 0),
    (8, "Shortbill Spearfish", 0),
    (9, "Long Snouted Lancetfish", 0),
    (10, "Great Barracuda", 0),
    (11, "Sickle Pomfret", 0),
    (12, "Pomfret", 0),
    (13, "Rainbow Runner", 0),
    (14, "Snake Mackerel", 0),
    (15, "Roudie Scolar", 0),
    # Bycatch (status=1)
    (16, "Shark", 1),
    (17, "Thresher Shark", 1),
    (18, "Opah", 1),
    (19, "Oilfish", 1),
    (20, "Mola Mola", 1),
    # Protected (status=2)
    (21, "Pelagic Stingray", 2),
    (22, "Striped Marlin", 2),
    (23, "Blue Marlin", 2),
    (24, "Black Marlin", 2),
    (25, "Indo Pacific Sailfish", 2),
    # Unknown (status=3)
    (26, "Unknown", 3),
]
```

---

## Step 4: Test (~5 min)

### Mock Mode Test
```bash
cd backend
MOCK_INFERENCE=true uv run uvicorn main:app --port 8000
# Upload test image via frontend
```

### Real Model Test
```bash
cd backend
uv run uvicorn main:app --port 8000
# Wait for "Model loaded!" message (~15-20s)
# Upload test image
```

---

## Step 5: Verify Alert Flow

1. Upload image with filename containing "stingray"
2. Verify CRITICAL alert appears (red)
3. Verify audio plays
4. Click Release button
5. Verify compliance updates

---

## Quick Reference: Species Codes

```
LEGAL:     ALB YFT BET SKJ DOL SWO WAH SSF LAF BAR SPF POM RRN SNM RSC
BYCATCH:   SHK THR OPA OIL MOL
PROTECTED: PLS STM BUM BKM SAI
OTHER:     UNK NOF
```

---

## Troubleshooting

### "Model not loaded"
- Check `models/catchlog-lora-adapter/` exists
- Check adapter files are present

### OOM on Mac
```python
# In inference.py, change:
DEVICE = "cpu"
torch_dtype=torch.float32
```

### Species Not Found
- Check model output codes match SPECIES_MAP
- Unknown codes default to "Unknown" status
