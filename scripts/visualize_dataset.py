#!/usr/bin/env python3
"""Visualize FOID dataset distributions and sample images."""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from PIL import Image
import random

DATA_DIR = Path("/Users/misran/Documents/misu/instalily-ai-hackathon/catchlog/data/foid_v012")
LABELS_FILE = DATA_DIR / "labels" / "foid_labels_bbox_v012.csv"
IMAGES_DIR = DATA_DIR / "images"
OUTPUT_DIR = Path("/Users/misran/Documents/misu/instalily-ai-hackathon/catchlog/.worktrees/data-exploration/scripts/output")
OUTPUT_DIR.mkdir(exist_ok=True)


def plot_species_distribution():
    """Create bar chart of fish species distribution."""
    df = pd.read_csv(LABELS_FILE)

    # Exclude Human and NoF
    fish_df = df[~df["label_l2"].isin(["HUMAN", "NoF"])]
    counts = fish_df["label_l1"].value_counts()

    fig, ax = plt.subplots(figsize=(14, 8))
    bars = ax.barh(counts.index[::-1], counts.values[::-1])

    # Color by status category
    legal = ["Albacore", "Bigeye tuna", "Yellowfin tuna", "Mahi mahi", "Skipjack tuna", "Swordfish", "Wahoo"]
    bycatch = ["Shark", "Opah", "Oilfish", "Black marlin", "Blue marlin", "Striped marlin",
               "Indo Pacific sailfish", "Shortbill spearfish", "Thresher shark"]
    protected = ["Pelagic stingray", "Mola mola"]

    for bar, species in zip(bars, counts.index[::-1]):
        if species in legal:
            bar.set_color("#22c55e")  # Green
        elif species in bycatch:
            bar.set_color("#eab308")  # Yellow
        elif species in protected:
            bar.set_color("#ef4444")  # Red
        else:
            bar.set_color("#6b7280")  # Gray

    ax.set_xlabel("Number of Bounding Boxes")
    ax.set_title("Fish Species Distribution in FOID Dataset\n(Green=Legal, Yellow=Bycatch, Red=Protected, Gray=Other)")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "species_distribution.png", dpi=150)
    print(f"✅ Saved species_distribution.png")


def plot_class_imbalance():
    """Visualize class imbalance for fine-tuning planning."""
    df = pd.read_csv(LABELS_FILE)
    fish_df = df[~df["label_l2"].isin(["HUMAN", "NoF"])]
    counts = fish_df["label_l1"].value_counts()

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Log scale
    ax1 = axes[0]
    ax1.bar(range(len(counts)), counts.values)
    ax1.set_yscale("log")
    ax1.set_xlabel("Species Index")
    ax1.set_ylabel("Count (log scale)")
    ax1.set_title("Class Imbalance (Log Scale)")

    # Pie chart of top categories
    ax2 = axes[1]
    top_5 = counts.head(5)
    other = counts[5:].sum()
    pie_data = list(top_5.values) + [other]
    pie_labels = list(top_5.index) + ["Other (21 species)"]
    ax2.pie(pie_data, labels=pie_labels, autopct="%1.1f%%", startangle=90)
    ax2.set_title("Fish Species Distribution")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "class_imbalance.png", dpi=150)
    print(f"✅ Saved class_imbalance.png")


def sample_images_by_species():
    """Sample and display images for key species."""
    df = pd.read_csv(LABELS_FILE)

    # Key species for POC
    poc_species = ["Albacore", "Bigeye tuna", "Yellowfin tuna", "Mahi mahi", "Shark"]

    fig, axes = plt.subplots(len(poc_species), 3, figsize=(15, 4 * len(poc_species)))

    for i, species in enumerate(poc_species):
        species_df = df[df["label_l1"] == species]
        sample_ids = species_df["img_id"].drop_duplicates().sample(min(3, len(species_df)), random_state=42)

        for j, img_id in enumerate(sample_ids):
            img_path = IMAGES_DIR / f"{img_id}.jpg"
            if img_path.exists():
                img = Image.open(img_path)
                ax = axes[i, j]
                ax.imshow(img)

                # Draw bboxes for this image
                img_bboxes = species_df[species_df["img_id"] == img_id]
                for _, row in img_bboxes.iterrows():
                    rect = plt.Rectangle(
                        (row["x_min"], row["y_min"]),
                        row["x_max"] - row["x_min"],
                        row["y_max"] - row["y_min"],
                        fill=False, edgecolor="lime", linewidth=2
                    )
                    ax.add_patch(rect)

                ax.set_title(f"{species}", fontsize=10)
                ax.axis("off")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "sample_images.png", dpi=150)
    print(f"✅ Saved sample_images.png")


def analyze_bbox_sizes():
    """Analyze bounding box sizes for detection model tuning."""
    df = pd.read_csv(LABELS_FILE)
    fish_df = df[~df["label_l2"].isin(["HUMAN", "NoF"])]

    # Calculate bbox dimensions
    fish_df = fish_df.copy()
    fish_df["width"] = fish_df["x_max"] - fish_df["x_min"]
    fish_df["height"] = fish_df["y_max"] - fish_df["y_min"]
    fish_df["area"] = fish_df["width"] * fish_df["height"]

    # Assume 1280x720 resolution
    fish_df["rel_area"] = fish_df["area"] / (1280 * 720)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Width distribution
    axes[0, 0].hist(fish_df["width"], bins=50, edgecolor="black")
    axes[0, 0].set_xlabel("Width (pixels)")
    axes[0, 0].set_ylabel("Count")
    axes[0, 0].set_title("Bounding Box Width Distribution")

    # Height distribution
    axes[0, 1].hist(fish_df["height"], bins=50, edgecolor="black")
    axes[0, 1].set_xlabel("Height (pixels)")
    axes[0, 1].set_ylabel("Count")
    axes[0, 1].set_title("Bounding Box Height Distribution")

    # Relative area
    axes[1, 0].hist(fish_df["rel_area"], bins=50, edgecolor="black")
    axes[1, 0].set_xlabel("Relative Area (% of image)")
    axes[1, 0].set_ylabel("Count")
    axes[1, 0].set_title("Bounding Box Relative Area")

    # Aspect ratio
    fish_df["aspect_ratio"] = fish_df["width"] / fish_df["height"]
    axes[1, 1].hist(fish_df["aspect_ratio"], bins=50, edgecolor="black", range=(0, 5))
    axes[1, 1].set_xlabel("Aspect Ratio (width/height)")
    axes[1, 1].set_ylabel("Count")
    axes[1, 1].set_title("Bounding Box Aspect Ratio")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "bbox_analysis.png", dpi=150)
    print(f"✅ Saved bbox_analysis.png")

    # Print summary stats
    print("\n📏 BBOX SIZE STATISTICS:")
    print(f"  Width:  min={fish_df['width'].min()}, max={fish_df['width'].max()}, median={fish_df['width'].median():.0f}")
    print(f"  Height: min={fish_df['height'].min()}, max={fish_df['height'].max()}, median={fish_df['height'].median():.0f}")
    print(f"  Area:   median={fish_df['area'].median():.0f}px², mean={fish_df['area'].mean():.0f}px²")
    print(f"  Rel area: median={fish_df['rel_area'].median()*100:.1f}%, mean={fish_df['rel_area'].mean()*100:.1f}%")


def main():
    print("=" * 60)
    print("FOID Dataset Visualization")
    print("=" * 60)

    plot_species_distribution()
    plot_class_imbalance()
    analyze_bbox_sizes()

    # Sample images (may be slow)
    print("\nSampling images (this may take a moment)...")
    sample_images_by_species()

    print(f"\n📂 All visualizations saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
