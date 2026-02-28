# Data Augmentation for Rare Species

**Purpose:** Boost protected species samples from 40 → 160+ for better model recall.

---

## Target Species

| Species | Current | Target | Multiplier |
|---------|---------|--------|------------|
| Pelagic stingray | 40 | 160 | 4x |
| Mola mola | 6 | 24 | 4x |

---

## Augmentation Script

```python
#!/usr/bin/env python3
"""Augment rare species images for fine-tuning."""

import os
import pandas as pd
from PIL import Image, ImageOps, ImageEnhance
from pathlib import Path
import shutil

# Config
DATA_DIR = Path("/home/hackathon/catchlog/data/foid_v012")  # VM path
LABELS_CSV = DATA_DIR / "labels" / "foid_labels_bbox_v012.csv"
IMAGES_DIR = DATA_DIR / "images"
OUTPUT_DIR = DATA_DIR / "images_augmented"
OUTPUT_LABELS = DATA_DIR / "labels" / "foid_labels_bbox_v012_augmented.csv"

# Species to augment
RARE_SPECIES = ["Pelagic stingray", "Mola mola"]

# Augmentation functions
AUGMENTATIONS = {
    "flip_h": lambda img: ImageOps.mirror(img),
    "flip_v": lambda img: ImageOps.flip(img),
    "bright": lambda img: ImageEnhance.Brightness(img).enhance(1.3),
    "dark": lambda img: ImageEnhance.Brightness(img).enhance(0.7),
}


def flip_bbox_horizontal(x_min, x_max, img_width):
    """Flip bbox x-coords for horizontal flip."""
    new_x_min = img_width - x_max
    new_x_max = img_width - x_min
    return new_x_min, new_x_max


def flip_bbox_vertical(y_min, y_max, img_height):
    """Flip bbox y-coords for vertical flip."""
    new_y_min = img_height - y_max
    new_y_max = img_height - y_min
    return new_y_min, new_y_max


def augment_image(img_id, img_path, annotations, aug_name, aug_func):
    """Create augmented image and update annotations."""
    img = Image.open(img_path)
    img_w, img_h = img.size

    # Apply augmentation
    aug_img = aug_func(img)

    # Save augmented image
    new_img_id = f"{img_id}_{aug_name}"
    new_img_path = OUTPUT_DIR / f"{new_img_id}.jpg"
    aug_img.save(new_img_path, quality=95)

    # Update annotations
    new_annotations = []
    for ann in annotations:
        new_ann = ann.copy()
        new_ann["img_id"] = new_img_id

        # Adjust bbox for flips
        if aug_name == "flip_h":
            new_ann["x_min"], new_ann["x_max"] = flip_bbox_horizontal(
                ann["x_min"], ann["x_max"], img_w
            )
        elif aug_name == "flip_v":
            new_ann["y_min"], new_ann["y_max"] = flip_bbox_vertical(
                ann["y_min"], ann["y_max"], img_h
            )

        new_annotations.append(new_ann)

    return new_annotations


def main():
    print("=" * 60)
    print("Data Augmentation for Rare Species")
    print("=" * 60)

    # Load labels
    df = pd.read_csv(LABELS_CSV)

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Filter to rare species
    rare_df = df[df["label_l1"].isin(RARE_SPECIES)]
    rare_images = rare_df["img_id"].unique()

    print(f"\nFound {len(rare_images)} images with rare species")
    print(f"Original annotations: {len(rare_df)}")

    # Augment each image
    all_new_annotations = []

    for img_id in rare_images:
        img_path = IMAGES_DIR / f"{img_id}.jpg"
        if not img_path.exists():
            continue

        # Get annotations for this image
        img_annotations = rare_df[rare_df["img_id"] == img_id].to_dict("records")

        # Apply each augmentation
        for aug_name, aug_func in AUGMENTATIONS.items():
            new_anns = augment_image(img_id, img_path, img_annotations, aug_name, aug_func)
            all_new_annotations.extend(new_anns)

    print(f"Created {len(all_new_annotations)} augmented annotations")

    # Combine original + augmented
    aug_df = pd.DataFrame(all_new_annotations)
    combined_df = pd.concat([df, aug_df], ignore_index=True)

    # Save combined labels
    combined_df.to_csv(OUTPUT_LABELS, index=False)
    print(f"\nSaved combined labels to: {OUTPUT_LABELS}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for species in RARE_SPECIES:
        original = len(df[df["label_l1"] == species])
        augmented = len(combined_df[combined_df["label_l1"] == species])
        print(f"{species}: {original} → {augmented} ({augmented/original:.1f}x)")


if __name__ == "__main__":
    main()
```

---

## Usage on VM

```bash
# SSH to VM
ssh hackathon@34.63.155.98

# Run augmentation
cd /home/hackathon/catchlog
python augment_rare_species.py

# Update notebook to use augmented labels
# Change LABELS_CSV to point to foid_labels_bbox_v012_augmented.csv
```

---

## Expected Output

```
Found 46 images with rare species
Original annotations: 46
Created 184 augmented annotations

SUMMARY
Pelagic stingray: 40 → 200 (5.0x)
Mola mola: 6 → 30 (5.0x)
```

---

## Integration with Fine-Tuning Notebook

In `catchlog_finetune.ipynb`, change:

```python
# Before
LABELS_CSV = "data/labels/foid_labels_bbox_v012.csv"

# After (if augmented)
LABELS_CSV = "data/labels/foid_labels_bbox_v012_augmented.csv"
```

The rest of the notebook works unchanged - it will automatically pick up the augmented images.
