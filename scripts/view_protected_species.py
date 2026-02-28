#!/usr/bin/env python3
"""View protected species samples."""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from PIL import Image

DATA_DIR = Path("/Users/misran/Documents/misu/instalily-ai-hackathon/catchlog/data/foid_v012")
LABELS_FILE = DATA_DIR / "labels" / "foid_labels_bbox_v012.csv"
IMAGES_DIR = DATA_DIR / "images"
OUTPUT_DIR = Path("/Users/misran/Documents/misu/instalily-ai-hackathon/catchlog/.worktrees/data-exploration/scripts/output")

df = pd.read_csv(LABELS_FILE)

# Get protected species
protected_species = ["Pelagic stingray", "Mola mola"]

fig, axes = plt.subplots(2, 4, figsize=(16, 8))

for i, species in enumerate(protected_species):
    species_df = df[df["label_l1"] == species]
    sample_ids = species_df["img_id"].unique()[:4]

    for j, img_id in enumerate(sample_ids):
        if j >= 4:
            break
        img_path = IMAGES_DIR / f"{img_id}.jpg"
        if img_path.exists():
            img = Image.open(img_path)
            ax = axes[i, j]
            ax.imshow(img)

            # Draw bbox
            img_bboxes = species_df[species_df["img_id"] == img_id]
            for _, row in img_bboxes.iterrows():
                rect = plt.Rectangle(
                    (row["x_min"], row["y_min"]),
                    row["x_max"] - row["x_min"],
                    row["y_max"] - row["y_min"],
                    fill=False, edgecolor="red", linewidth=3
                )
                ax.add_patch(rect)

            ax.set_title(f"{species}", fontsize=10)
            ax.axis("off")

# Fill empty slots if species has fewer than 4 samples
for i in range(2):
    for j in range(4):
        if not axes[i, j].has_data():
            axes[i, j].axis("off")
            axes[i, j].text(0.5, 0.5, "N/A", ha="center", va="center", transform=axes[i, j].transAxes)

plt.suptitle("Protected Species Samples (Red = Bounding Box)", fontsize=14)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "protected_species.png", dpi=150)
print(f"✅ Saved protected_species.png")
