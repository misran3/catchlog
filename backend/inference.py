# backend/inference.py
"""Mock inference module - swap for real model later."""

import random
from dataclasses import dataclass
from PIL import Image


@dataclass
class InferenceResult:
    """Result from running inference on an image."""
    species: str
    confidence: float
    bbox: list[int]  # [x1, y1, x2, y2]


# Weighted species distribution for realistic demo
# Format: (species_name, weight)
SPECIES_WEIGHTS = [
    ("Albacore Tuna", 30),  # Legal - common
    ("Bigeye Tuna", 25),    # Legal - common
    ("Mahi-Mahi", 15),      # Legal - less common
    ("Blue Shark", 20),     # Bycatch
    ("Sea Turtle", 8),      # Protected - rare
    ("Unknown", 2),         # Unknown - very rare
]


def _weighted_random_species() -> str:
    """Pick a species based on weighted distribution."""
    species_list = [s for s, _ in SPECIES_WEIGHTS]
    weights = [w for _, w in SPECIES_WEIGHTS]
    return random.choices(species_list, weights=weights, k=1)[0]


def _random_bbox(width: int, height: int) -> list[int]:
    """Generate a random bounding box within image bounds."""
    # Box should be 20-40% of image size
    box_w = random.randint(int(width * 0.2), int(width * 0.4))
    box_h = random.randint(int(height * 0.2), int(height * 0.4))

    # Random position (ensure box fits)
    x1 = random.randint(0, width - box_w)
    y1 = random.randint(0, height - box_h)
    x2 = x1 + box_w
    y2 = y1 + box_h

    return [x1, y1, x2, y2]


def run_inference(image: Image.Image) -> InferenceResult:
    """
    Run mock inference on an image.

    In production, this would:
    1. Preprocess image for PaliGemma
    2. Run model forward pass
    3. Parse detection output

    For now, returns random realistic results.
    """
    width, height = image.size

    return InferenceResult(
        species=_weighted_random_species(),
        confidence=round(random.uniform(0.75, 0.98), 2),
        bbox=_random_bbox(width, height),
    )


# === Interface for swapping in real model ===

_model = None


def load_model(model_path: str | None = None) -> None:
    """
    Load the inference model.

    For mock: does nothing.
    For real model: loads PaliGemma + LoRA weights.
    """
    global _model
    # TODO: Load real model when ready
    # from transformers import AutoProcessor, PaliGemmaForConditionalGeneration
    # _model = PaliGemmaForConditionalGeneration.from_pretrained(...)
    _model = "mock"


def is_model_loaded() -> bool:
    """Check if model is loaded."""
    return _model is not None
