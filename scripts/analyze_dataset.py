#!/usr/bin/env python3
"""Analyze FOID dataset for CatchLog project."""

import pandas as pd
from pathlib import Path
from collections import Counter
import json

DATA_DIR = Path("/Users/misran/Documents/misu/instalily-ai-hackathon/catchlog/data/foid_v012")
LABELS_FILE = DATA_DIR / "labels" / "foid_labels_bbox_v012.csv"
FREQ_FILE = DATA_DIR / "labels" / "foid_labels_bbox_v012_freq.csv"
IMAGES_DIR = DATA_DIR / "images"


def main():
    print("=" * 60)
    print("FOID v0.12 Dataset Analysis for CatchLog")
    print("=" * 60)

    # Load labels
    df = pd.read_csv(LABELS_FILE)
    freq_df = pd.read_csv(FREQ_FILE)

    # Basic stats
    print("\n📊 BASIC STATISTICS")
    print("-" * 40)
    total_images = len(list(IMAGES_DIR.glob("*.jpg")))
    unique_images = df["img_id"].nunique()
    total_bboxes = len(df)
    print(f"Total image files: {total_images:,}")
    print(f"Images with labels: {unique_images:,}")
    print(f"Total bounding boxes: {total_bboxes:,}")
    print(f"Avg bboxes per image: {total_bboxes / unique_images:.2f}")

    # Species distribution
    print("\n🐟 SPECIES DISTRIBUTION (by bbox count)")
    print("-" * 40)
    for _, row in freq_df.sort_values("count", ascending=False).iterrows():
        pct = (row["count"] / total_bboxes) * 100
        print(f"  {row['label_l1']:<25} ({row['label_l2']:<6}): {row['count']:>6,} ({pct:>5.1f}%)")

    # Category groupings for UI
    print("\n🎯 CATEGORY GROUPINGS (for CatchLog UI)")
    print("-" * 40)

    # Map to regulatory categories
    regulatory = {
        "LEGAL_TARGET": ["ALB", "BET", "YFT", "DOL", "SKJ"],  # Target species
        "BYCATCH": ["SHARK", "PLS", "OTH", "LAG", "OIL"],  # Bycatch - release required
        "BILLFISH": ["BILL"],  # Special regulation - varies by region
        "IGNORE": ["HUMAN", "NoF"],  # Not fish
        "UNKNOWN": ["Unknown"],  # Needs review
    }

    code_to_l1 = dict(zip(freq_df["label_l2"], freq_df["label_l1"]))
    code_to_count = dict(zip(freq_df["label_l2"], freq_df["count"]))

    for category, codes in regulatory.items():
        total = sum(code_to_count.get(c, 0) for c in codes)
        print(f"\n  {category}: {total:,} bboxes")
        for code in codes:
            if code in code_to_count:
                print(f"    - {code_to_l1.get(code, code)}: {code_to_count[code]:,}")

    # Image size analysis (sample)
    print("\n📐 IMAGE DIMENSIONS (sample)")
    print("-" * 40)
    sample_bboxes = df.head(1000)
    max_x = sample_bboxes["x_max"].max()
    max_y = sample_bboxes["y_max"].max()
    print(f"Max x_max in sample: {max_x}")
    print(f"Max y_max in sample: {max_y}")
    print(f"Likely resolution: ~{max_x}x{max_y}")

    # Multi-object images
    print("\n🔢 MULTI-OBJECT IMAGES")
    print("-" * 40)
    bboxes_per_image = df.groupby("img_id").size()
    print(f"Images with 1 bbox: {(bboxes_per_image == 1).sum():,}")
    print(f"Images with 2 bboxes: {(bboxes_per_image == 2).sum():,}")
    print(f"Images with 3+ bboxes: {(bboxes_per_image >= 3).sum():,}")
    print(f"Max bboxes in one image: {bboxes_per_image.max()}")

    # Fish-only analysis (exclude Human, NoF)
    print("\n🎣 FISH-ONLY ANALYSIS")
    print("-" * 40)
    fish_df = df[~df["label_l2"].isin(["HUMAN", "NoF"])]
    fish_images = fish_df["img_id"].nunique()
    fish_bboxes = len(fish_df)
    print(f"Images with fish: {fish_images:,}")
    print(f"Fish bounding boxes: {fish_bboxes:,}")
    print(f"Fish species detected: {fish_df['label_l1'].nunique()}")

    fish_counts = fish_df["label_l1"].value_counts()
    print("\nTop 10 fish species:")
    for species, count in fish_counts.head(10).items():
        print(f"  {species}: {count:,}")

    # Class imbalance analysis
    print("\n⚖️ CLASS IMBALANCE ANALYSIS")
    print("-" * 40)
    fish_freq = freq_df[~freq_df["label_l2"].isin(["HUMAN", "NoF"])]
    max_class = fish_freq["count"].max()
    min_class = fish_freq["count"].min()
    print(f"Most common fish: {fish_freq.loc[fish_freq['count'].idxmax(), 'label_l1']} ({max_class:,})")
    print(f"Least common fish: {fish_freq.loc[fish_freq['count'].idxmin(), 'label_l1']} ({min_class:,})")
    print(f"Imbalance ratio: {max_class / min_class:.0f}:1")

    # Fine-tuning recommendations
    print("\n💡 FINE-TUNING RECOMMENDATIONS")
    print("-" * 40)

    # Calculate recommended samples
    fish_freq_sorted = fish_freq.sort_values("count", ascending=False)

    print("\n1. BALANCED SUBSET (for initial fine-tuning):")
    print("   Target: ~500 samples per class, max 5000 total")
    balanced_total = 0
    for _, row in fish_freq_sorted.iterrows():
        samples = min(row["count"], 500)
        balanced_total += samples
        print(f"   {row['label_l1']}: {samples}")
    print(f"   Total: {balanced_total:,} samples")

    print("\n2. STRATIFIED SUBSET (maintain distribution):")
    print("   Target: 10% of data (~3500 fish bboxes)")
    stratified_total = 0
    for _, row in fish_freq_sorted.iterrows():
        samples = max(1, int(row["count"] * 0.1))
        stratified_total += samples
        print(f"   {row['label_l1']}: {samples}")
    print(f"   Total: {stratified_total:,} samples")

    print("\n3. KEY SPECIES SUBSET (CatchLog POC):")
    poc_species = ["Albacore", "Bigeye tuna", "Yellowfin tuna", "Mahi mahi", "Shark"]
    print("   Focus on species in master spec:")
    poc_total = 0
    for species in poc_species:
        count = fish_counts.get(species, 0)
        samples = min(count, 1000)
        poc_total += samples
        print(f"   {species}: {samples} (of {count:,} available)")
    print(f"   Total: {poc_total:,} samples")

    # Output summary for integration
    print("\n📝 UI/BACKEND INTEGRATION NOTES")
    print("-" * 40)
    print("""
1. SPECIES MAPPING NEEDED:
   - Current backend has 6 species (Albacore Tuna, Bigeye Tuna, Mahi-Mahi, Blue Shark, Sea Turtle, Unknown)
   - Dataset has 27+ species - need mapping strategy

2. BBOX FORMAT:
   - Dataset: [x_min, x_max, y_min, y_max]
   - Backend expects: [x1, y1, x2, y2]
   - Conversion: [x_min, y_min, x_max, y_max]

3. LABEL HIERARCHY:
   - label_l1: Full name (e.g., "Albacore")
   - label_l2: Code (e.g., "ALB")
   - Consider using codes for inference, names for UI

4. MISSING FROM CURRENT DESIGN:
   - Sea Turtle: NOT in dataset (add synthetic or skip for POC)
   - Need to map "Shark" to "Blue Shark" or use generic

5. REGULATORY MAPPING:
   - Dataset doesn't include regulatory status
   - Backend hardcodes: legal, bycatch, protected
   - Need external regulation lookup or manual mapping
""")

    # Export species mapping for backend
    species_mapping = {
        "Albacore": {"status": "legal", "backend_name": "Albacore Tuna"},
        "Bigeye tuna": {"status": "legal", "backend_name": "Bigeye Tuna"},
        "Yellowfin tuna": {"status": "legal", "backend_name": "Yellowfin Tuna"},
        "Mahi mahi": {"status": "legal", "backend_name": "Mahi-Mahi"},
        "Shark": {"status": "bycatch", "backend_name": "Blue Shark"},
        "Skipjack tuna": {"status": "legal", "backend_name": "Skipjack Tuna"},
        "Wahoo": {"status": "legal", "backend_name": "Wahoo"},
        "Opah": {"status": "bycatch", "backend_name": "Opah"},
        "Oilfish": {"status": "bycatch", "backend_name": "Oilfish"},
        "Unknown": {"status": "unknown", "backend_name": "Unknown"},
        # Billfish - varies by region, default to bycatch
        "Black marlin": {"status": "bycatch", "backend_name": "Black Marlin"},
        "Blue marlin": {"status": "bycatch", "backend_name": "Blue Marlin"},
        "Striped marlin": {"status": "bycatch", "backend_name": "Striped Marlin"},
        "Swordfish": {"status": "legal", "backend_name": "Swordfish"},  # Often legal target
        "Indo Pacific sailfish": {"status": "bycatch", "backend_name": "Sailfish"},
        "Shortbill spearfish": {"status": "bycatch", "backend_name": "Spearfish"},
        # Protected species (add manually for POC)
        "Pelagic stingray": {"status": "protected", "backend_name": "Pelagic Stingray"},
        "Mola mola": {"status": "protected", "backend_name": "Ocean Sunfish"},
    }

    with open("species_mapping.json", "w") as f:
        json.dump(species_mapping, f, indent=2)
    print("\n✅ Exported species_mapping.json for backend integration")


if __name__ == "__main__":
    main()
