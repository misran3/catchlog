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
    ("Albacore Tuna", 35),    # Legal - most common
    ("Yellowfin Tuna", 20),   # Legal - common
    ("Bigeye Tuna", 10),      # Legal
    ("Mahi-Mahi", 5),         # Legal
    ("Shark", 15),            # Bycatch
    ("Opah", 8),              # Bycatch
    ("Pelagic Stingray", 5),  # Protected - rare
    ("Unknown", 2),           # Unknown - very rare
]

# Test-only: force specific species for deterministic testing
_forced_species: str | None = None


def set_next_species(species: str | None) -> None:
    """Force next inference to return specific species. For testing only."""
    global _forced_species
    _forced_species = species


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
    global _forced_species

    width, height = image.size

    # Use forced species if set (for testing), otherwise random
    if _forced_species:
        species = _forced_species
        _forced_species = None  # Reset after use
    else:
        species = _weighted_random_species()

    return InferenceResult(
        species=species,
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
