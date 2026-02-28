#!/usr/bin/env python3
"""Extract demo images from FOID dataset for UI testing."""

import json
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

# Species to extract: (dataset_label, slug, count, is_protected)
TARGET_SPECIES = [
    ("Albacore", "albacore-tuna", 3, False),
    ("Bigeye tuna", "bigeye-tuna", 2, False),
    ("Mahi mahi", "mahi-mahi", 2, False),
    ("Yellowfin tuna", "yellowfin-tuna", 3, False),
    ("Shark", "shark", 3, False),
    ("Opah", "opah", 2, False),
    ("Pelagic stingray", "pelagic-stingray", 3, True),  # Protected - take largest by bbox
    ("Unknown", "unknown", 2, False),
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
    bbox_data = {}  # Store bbox coordinates for each image

    for dataset_label, slug, count, is_protected in TARGET_SPECIES:
        print(f"\n{dataset_label} -> {slug}")

        # Filter to this species
        species_df = fish_df[fish_df["label_l1"] == dataset_label]
        print(f"  Total bboxes: {len(species_df)}")

        if is_protected:
            # For protected species: take largest by bbox area (no threshold)
            sorted_df = species_df.nlargest(count, "bbox_area")
            sampled_rows = sorted_df.to_dict("records")
            print(f"  Taking {len(sampled_rows)} largest by bbox area (protected species)")
        else:
            # For other species: filter to prominent bboxes (>5% of image)
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
            # Get the row data for sampled images (take first bbox per image)
            sampled_rows = []
            for img_id in sampled_ids:
                row = prominent_df[prominent_df["img_id"] == img_id].iloc[0].to_dict()
                sampled_rows.append(row)

        # Copy images and save bbox data
        for i, row in enumerate(sampled_rows, 1):
            img_id = row["img_id"]
            src = IMAGES_DIR / f"{img_id}.jpg"
            filename = f"{slug}_{i:03d}.jpg"
            dst = OUTPUT_DIR / filename

            if src.exists():
                shutil.copy(src, dst)
                # Convert FOID bbox format [x_min, x_max, y_min, y_max] to [x1, y1, x2, y2]
                bbox = [
                    int(row["x_min"]),
                    int(row["y_min"]),
                    int(row["x_max"]),
                    int(row["y_max"]),
                ]
                bbox_data[filename] = {"bbox": bbox}
                print(f"  Copied: {filename} (bbox: {bbox})")
                total_extracted += 1
            else:
                print(f"  WARNING: Source not found: {src}")

    # Save bbox data to JSON
    bbox_file = OUTPUT_DIR / "demo_bboxes.json"
    with open(bbox_file, "w") as f:
        json.dump(bbox_data, f, indent=2)
    print(f"\nSaved bbox data to: {bbox_file}")

    print(f"\n{'=' * 40}")
    print(f"Total images extracted: {total_extracted}")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    random.seed(42)  # Reproducible sampling
    extract_images()
