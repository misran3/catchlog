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
