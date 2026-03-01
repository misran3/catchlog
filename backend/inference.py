# backend/inference.py
"""PaliGemma inference with LoRA adapter for fish species detection."""

import os
import re
import random
from dataclasses import dataclass
from pathlib import Path
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
    "SHK": {"name": "Shark", "status": "protected"},  # DEMO: Changed for demo
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

# Filename mappings for mock mode
FILENAME_TO_SPECIES = {
    "albacore": "Albacore Tuna",
    "albacore-tuna": "Albacore Tuna",
    "yellowfin": "Yellowfin Tuna",
    "yellowfin-tuna": "Yellowfin Tuna",
    "bigeye": "Bigeye Tuna",
    "bigeye-tuna": "Bigeye Tuna",
    "mahi": "Mahi-Mahi",
    "mahi-mahi": "Mahi-Mahi",
    "shark": "Shark",
    "opah": "Opah",
    "stingray": "Pelagic Stingray",
    "pelagic-stingray": "Pelagic Stingray",
    "protected": "Pelagic Stingray",
    "marlin": "Blue Marlin",
    "blue-marlin": "Blue Marlin",
    "unknown": "Unknown",
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
        # Note: PaliGemma order is [y1, x1, y2, x2]
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
# MODEL STATE
# ============================================================

_model = None
_processor = None
_device = None
ADAPTER_PATH = Path(__file__).parent / "models" / "catchlog-lora-adapter"
BASE_MODEL_ID = "google/paligemma2-3b-pt-224"


def load_model(adapter_path: str | None = None) -> None:
    """Load PaliGemma + LoRA adapter."""
    global _model, _processor, _device

    # Check for mock mode
    if os.getenv("MOCK_INFERENCE") == "true":
        print("MOCK_INFERENCE=true - using mock inference")
        _model = "mock"
        return

    import torch
    from transformers import PaliGemmaProcessor, PaliGemmaForConditionalGeneration
    from peft import PeftModel

    adapter_path = adapter_path or str(ADAPTER_PATH)

    # Determine device
    if torch.backends.mps.is_available():
        _device = "mps"
    elif torch.cuda.is_available():
        _device = "cuda"
    else:
        _device = "cpu"

    print(f"Loading processor from {BASE_MODEL_ID}...")
    _processor = PaliGemmaProcessor.from_pretrained(BASE_MODEL_ID)

    print(f"Loading base model to {_device}...")
    dtype = torch.float16 if _device != "cpu" else torch.float32
    _model = PaliGemmaForConditionalGeneration.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=dtype,
        device_map=_device,
    )

    print(f"Loading LoRA adapter from {adapter_path}...")
    _model = PeftModel.from_pretrained(_model, adapter_path)
    _model.eval()

    print(f"Model loaded on {_device}!")


def is_model_loaded() -> bool:
    """Check if model is loaded."""
    return _model is not None


def warmup_model() -> None:
    """Run dummy inference to JIT compile (for MPS)."""
    if _model == "mock":
        return
    if _model is None:
        return

    print("Warming up model...")
    dummy = Image.new("RGB", (224, 224), color="blue")
    _run_raw_inference(dummy)
    print("Warmup complete!")


def _run_raw_inference(image: Image.Image) -> str:
    """Run inference, return raw model output."""
    import torch

    dtype = torch.float16 if _device != "cpu" else torch.float32
    inputs = _processor(
        text="<image>detect fish",
        images=image.convert("RGB"),
        return_tensors="pt"
    ).to(_device, dtype=dtype)

    with torch.no_grad():
        output = _model.generate(**inputs, max_new_tokens=256)

    return _processor.decode(output[0], skip_special_tokens=False)


# ============================================================
# MOCK INFERENCE
# ============================================================

_forced_species: str | None = None


def set_next_species(species: str | None) -> None:
    """Force next inference to return specific species. For testing only."""
    global _forced_species
    _forced_species = species


def _weighted_random_species() -> tuple[str, str]:
    """Pick a species based on weighted distribution."""
    choices = [
        ("Albacore Tuna", "legal", 35),
        ("Yellowfin Tuna", "legal", 20),
        ("Bigeye Tuna", "legal", 10),
        ("Mahi-Mahi", "legal", 5),
        ("Shark", "bycatch", 15),
        ("Opah", "bycatch", 8),
        ("Pelagic Stingray", "protected", 5),
        ("Unknown", "unknown", 2),
    ]
    species_status = [(s, st) for s, st, _ in choices]
    weights = [w for _, _, w in choices]
    return random.choices(species_status, weights=weights, k=1)[0]


def _random_bbox(width: int, height: int) -> list[int]:
    """Generate a random bounding box within image bounds."""
    box_w = random.randint(int(width * 0.2), int(width * 0.4))
    box_h = random.randint(int(height * 0.2), int(height * 0.4))
    x1 = random.randint(0, max(1, width - box_w))
    y1 = random.randint(0, max(1, height - box_h))
    return [x1, y1, x1 + box_w, y1 + box_h]


def _parse_species_from_filename(filename: str | None) -> str | None:
    """Extract species from filename for mock mode."""
    if not filename:
        return None

    stem = Path(filename).stem.lower()
    # Remove trailing numbers like _001
    slug = re.sub(r"_\d+$", "", stem)

    # Check direct match
    if slug in FILENAME_TO_SPECIES:
        return FILENAME_TO_SPECIES[slug]

    # Check partial match
    for key, species in FILENAME_TO_SPECIES.items():
        if key in slug:
            return species

    return None


def _mock_inference(image: Image.Image, filename: str | None) -> InferenceResult:
    """Return mock result based on filename or random."""
    global _forced_species

    width, height = image.size

    # Priority 1: Forced species (for testing)
    if _forced_species:
        species = _forced_species
        _forced_species = None
        return InferenceResult(
            species=species,
            confidence=round(random.uniform(0.80, 0.95), 2),
            bbox=_random_bbox(width, height),
        )

    # Priority 2: Parse from filename
    parsed = _parse_species_from_filename(filename)
    if parsed:
        return InferenceResult(
            species=parsed,
            confidence=round(random.uniform(0.80, 0.95), 2),
            bbox=_random_bbox(width, height),
        )

    # Priority 3: Weighted random
    species, _ = _weighted_random_species()
    return InferenceResult(
        species=species,
        confidence=round(random.uniform(0.75, 0.95), 2),
        bbox=_random_bbox(width, height),
    )


# ============================================================
# PUBLIC INTERFACE
# ============================================================

def run_inference(image: Image.Image, filename: str | None = None) -> InferenceResult:
    """
    Run inference on an image, return primary detection.

    If MOCK_INFERENCE=true or model not loaded, returns mock results.
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

    # Parse detections from model output
    detections = parse_detections(raw_output, img_width, img_height)

    # Select most critical detection
    primary = select_primary_detection(detections)

    if primary is None:
        # No fish detected - return Unknown
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
