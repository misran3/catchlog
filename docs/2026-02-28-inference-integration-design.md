# CatchLog Inference Integration Design

**Date:** 2026-02-28
**Scope:** Replace mock inference with real PaliGemma model
**Target:** Mac M1 Pro 16GB with MPS acceleration

---

## Overview

This module bridges the fine-tuned PaliGemma model output to the backend API format. It replaces `backend/inference.py` (mock) with real model inference.

### Data Flow

```
Image (PIL)
    → Preprocess (resize to 224x224)
    → PaliGemma inference (MPS)
    → Parse output text "<loc...> ALB ; <loc...> SHK"
    → Convert to detections list
    → Prioritize by status (protected > bycatch > unknown > legal)
    → Return primary detection with pixel bbox + mapped species name
```

### Performance Targets

| Metric | Target |
|--------|--------|
| Cold start (model load + warmup) | ~15-20 seconds |
| Inference per image | 1-3 seconds |
| Memory usage | ~4-6 GB |

---

## Architecture

### Files to Modify/Create

```
backend/
├── inference.py          # REPLACE - real model inference
├── models/
│   └── catchlog-lora-adapter/   # NEW - LoRA weights from VM
│       ├── adapter_config.json
│       └── adapter_model.safetensors
└── requirements: transformers, peft, torch
```

### Dependencies to Add

```toml
# backend/pyproject.toml - add these
dependencies = [
    # ... existing ...
    "torch>=2.1.0",
    "transformers>=4.47.0",
    "peft>=0.7.0",
    "accelerate>=0.25.0",
]
```

---

## Species Mapping

Maps model output codes to display names and regulatory status.

```python
SPECIES_MAP = {
    # Legal (priority 4 - lowest)
    "ALB": {"name": "Albacore Tuna", "status": "legal"},
    "YFT": {"name": "Yellowfin Tuna", "status": "legal"},
    "BET": {"name": "Bigeye Tuna", "status": "legal"},
    "DOL": {"name": "Mahi-Mahi", "status": "legal"},
    "SKJ": {"name": "Skipjack Tuna", "status": "legal"},
    "SWO": {"name": "Swordfish", "status": "legal"},

    # Bycatch (priority 2)
    "SHK": {"name": "Shark", "status": "bycatch"},
    "OPA": {"name": "Opah", "status": "bycatch"},
    "OIL": {"name": "Oilfish", "status": "bycatch"},

    # Protected (priority 1 - highest)
    "PLS": {"name": "Pelagic Stingray", "status": "protected"},
    "BUM": {"name": "Blue Marlin", "status": "protected"},
    "STM": {"name": "Striped Marlin", "status": "protected"},

    # Unknown (priority 3)
    "UNK": {"name": "Unknown", "status": "unknown"},

    # Ignore (not returned as detections)
    "NOF": {"name": "No Fish", "status": "ignore"},
}

STATUS_PRIORITY = {
    "protected": 1,  # Always surface these
    "bycatch": 2,
    "unknown": 3,
    "legal": 4,
}
```

**Note:** These codes assume the fine-tuning notebook is updated per `docs/fine-tuning-review.md` recommendations to use distinct codes (SWO, STM, BUM) instead of shared codes (BILL).

---

## Output Parsing

PaliGemma outputs detections in this format:
```
<loc0123><loc0456><loc0789><loc0999> ALB ; <loc0100><loc0200><loc0300><loc0400> SHK
```

**Important:** PaliGemma uses `[y1, x1, y2, x2]` order. Backend expects `[x1, y1, x2, y2]`.

```python
import re
from dataclasses import dataclass

DETECTION_PATTERN = r'<loc(\d{4})><loc(\d{4})><loc(\d{4})><loc(\d{4})>\s*(\w+)'


@dataclass
class InferenceResult:
    """Result from running inference on an image."""
    species: str
    confidence: float
    bbox: list[int]  # [x1, y1, x2, y2] in pixels


def parse_detections(output_text: str, img_width: int, img_height: int) -> list[dict]:
    """Parse PaliGemma output into detection dicts."""
    detections = []

    for match in re.finditer(DETECTION_PATTERN, output_text):
        y1_norm, x1_norm, y2_norm, x2_norm, species_code = match.groups()

        # Skip ignored classes
        if species_code in ("NOF", "HUMAN"):
            continue

        # Convert normalized (0-1023) to pixel coordinates
        # Note: PaliGemma order is [y1, x1, y2, x2]
        x1 = int(int(x1_norm) / 1023 * img_width)
        y1 = int(int(y1_norm) / 1023 * img_height)
        x2 = int(int(x2_norm) / 1023 * img_width)
        y2 = int(int(y2_norm) / 1023 * img_height)

        # Look up species info (default to Unknown)
        species_info = SPECIES_MAP.get(species_code, SPECIES_MAP["UNK"])

        detections.append({
            "species": species_info["name"],
            "status": species_info["status"],
            "bbox": [x1, y1, x2, y2],
            "confidence": 0.85,  # Hardcoded - see "Future: Confidence Scores"
        })

    return detections


def select_primary_detection(detections: list[dict]) -> dict | None:
    """Select most critical detection (protected > bycatch > unknown > legal)."""
    if not detections:
        return None

    return min(detections, key=lambda d: STATUS_PRIORITY.get(d["status"], 99))
```

---

## Model Loading & Inference

### Model Loading (Startup)

```python
from transformers import PaliGemmaProcessor, PaliGemmaForConditionalGeneration
from peft import PeftModel
import torch
from PIL import Image

# Global model state
_model = None
_processor = None
DEVICE = "mps"  # Apple Silicon
ADAPTER_PATH = "models/catchlog-lora-adapter"
BASE_MODEL_ID = "google/paligemma2-3b-pt-224"


def load_model(adapter_path: str = ADAPTER_PATH) -> None:
    """Load PaliGemma + LoRA adapter. Call once at startup."""
    global _model, _processor

    print(f"Loading processor from {BASE_MODEL_ID}...")
    _processor = PaliGemmaProcessor.from_pretrained(BASE_MODEL_ID)

    print(f"Loading base model...")
    _model = PaliGemmaForConditionalGeneration.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.float16,
        device_map="mps",
    )

    print(f"Loading LoRA adapter from {adapter_path}...")
    _model = PeftModel.from_pretrained(_model, adapter_path)
    _model.eval()

    print("Model loaded successfully!")


def is_model_loaded() -> bool:
    """Check if model is loaded."""
    return _model is not None and _processor is not None
```

### Warm-up (Eliminate Cold Start)

First inference triggers MPS JIT compilation. Run a dummy inference at startup to eliminate this latency during demo.

```python
def warmup_model() -> None:
    """Run dummy inference to JIT compile MPS kernels."""
    if not is_model_loaded():
        raise RuntimeError("Model not loaded")

    print("Running warmup inference...")
    dummy_image = Image.new("RGB", (224, 224), color="blue")
    _ = _run_raw_inference(dummy_image)
    print("Warmup complete!")


def _run_raw_inference(image: Image.Image) -> str:
    """Run inference, return raw model output text."""
    inputs = _processor(
        text="<image>detect fish",
        images=image.convert("RGB"),
        return_tensors="pt"
    ).to(DEVICE, dtype=torch.float16)

    with torch.no_grad():
        output = _model.generate(**inputs, max_new_tokens=256)

    return _processor.decode(output[0], skip_special_tokens=False)
```

### FastAPI Integration

```python
# backend/main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize model on startup."""
    print("=" * 50)
    print("Starting CatchLog Backend")
    print("=" * 50)

    # Initialize database
    init_db()

    # Load model + warmup (total ~15-20s)
    load_model()
    warmup_model()

    print("=" * 50)
    print("Server ready - no cold start!")
    print("=" * 50)

    yield

app = FastAPI(lifespan=lifespan, ...)
```

---

## Public Interface

The main function called by `agent.py`:

```python
def run_inference(image: Image.Image) -> InferenceResult:
    """
    Run inference on an image, return primary detection.

    Args:
        image: PIL Image to analyze

    Returns:
        InferenceResult with species name, confidence, and pixel bbox

    Raises:
        RuntimeError: If model not loaded
        ValueError: If no fish detected
    """
    if not is_model_loaded():
        raise RuntimeError("Model not loaded. Call load_model() first.")

    img_width, img_height = image.size

    # Run model
    raw_output = _run_raw_inference(image)

    # Parse detections
    detections = parse_detections(raw_output, img_width, img_height)

    # Select primary (most critical) detection
    primary = select_primary_detection(detections)

    if primary is None:
        # No fish detected - return Unknown
        return InferenceResult(
            species="Unknown",
            confidence=0.5,
            bbox=[0, 0, img_width, img_height],  # Full frame
        )

    return InferenceResult(
        species=primary["species"],
        confidence=primary["confidence"],
        bbox=primary["bbox"],
    )
```

---

## Demo Workflow

1. **Before demo (2-3 min):**
   ```bash
   cd backend && uv run uvicorn main:app --port 8000
   # Wait for "Server ready - no cold start!" message
   ```

2. **During demo:**
   - First upload is fast (~1-3s)
   - All subsequent uploads are fast

3. **If server crashes:**
   - Restart and wait 15-20s for model reload
   - Have backup images ready during reload

---

## Future: Confidence Scores

Currently hardcoded to `0.85`. To add real confidence from model:

### Option A: Token Log Probabilities (Recommended)

Extract logprobs during generation without retraining:

```python
def _run_raw_inference_with_confidence(image: Image.Image) -> tuple[str, float]:
    """Run inference with confidence estimation."""
    inputs = _processor(
        text="<image>detect fish",
        images=image.convert("RGB"),
        return_tensors="pt"
    ).to(DEVICE, dtype=torch.float16)

    with torch.no_grad():
        output = _model.generate(
            **inputs,
            max_new_tokens=256,
            output_scores=True,
            return_dict_in_generate=True,
        )

    # Get token probabilities
    scores = output.scores  # List of logits per generated token
    probs = [torch.softmax(s, dim=-1).max().item() for s in scores]

    # Average probability of generated tokens as confidence proxy
    avg_confidence = sum(probs) / len(probs) if probs else 0.5

    decoded = _processor.decode(output.sequences[0], skip_special_tokens=False)
    return decoded, avg_confidence
```

### Option B: Train with Confidence in Output

Modify training format to include confidence:
```
<loc0123><loc0456><loc0789><loc0999> ALB 0.92 ; ...
```

Requires retraining - not recommended for hackathon timeline.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Model not loaded | Raise `RuntimeError` |
| No fish detected | Return "Unknown" with full-frame bbox |
| Unknown species code | Map to "Unknown" status |
| Image load failure | Handled by FastAPI (400 error) |
| MPS out of memory | Restart server, reduce batch size |

---

## Testing

### Manual Test

```bash
# Terminal 1: Start server
cd backend && uv run uvicorn main:app --reload --port 8000

# Terminal 2: Test inference
curl -X POST http://localhost:8000/api/upload \
  -F "file=@test_image.jpg"
```

### Unit Test

```python
# backend/tests/test_inference.py
def test_parse_detections():
    output = "<loc0100><loc0200><loc0300><loc0400> ALB"
    detections = parse_detections(output, 1280, 720)

    assert len(detections) == 1
    assert detections[0]["species"] == "Albacore Tuna"
    assert detections[0]["status"] == "legal"


def test_select_primary_protected():
    detections = [
        {"species": "Albacore Tuna", "status": "legal", "bbox": [0,0,100,100]},
        {"species": "Pelagic Stingray", "status": "protected", "bbox": [0,0,50,50]},
    ]
    primary = select_primary_detection(detections)

    assert primary["species"] == "Pelagic Stingray"  # Protected takes priority
```

---

## Checklist

- [ ] Download LoRA adapter from VM to `backend/models/catchlog-lora-adapter/`
- [ ] Add torch/transformers/peft to `pyproject.toml`
- [ ] Replace mock `inference.py` with real implementation
- [ ] Update `main.py` lifespan to load model + warmup
- [ ] Test with sample images from each species category
- [ ] Verify protected species triggers alert correctly
