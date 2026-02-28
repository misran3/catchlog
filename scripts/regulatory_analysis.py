#!/usr/bin/env python3
"""Analyze species by regulatory status for CatchLog POC."""

import pandas as pd
from pathlib import Path
import json

DATA_DIR = Path("/Users/misran/Documents/misu/instalily-ai-hackathon/catchlog/data/foid_v012")
LABELS_FILE = DATA_DIR / "labels" / "foid_labels_bbox_v012.csv"

# Regulatory status mapping based on real fishing regulations
# Sources: NOAA, WCPFC, IATTC regulations
REGULATORY_STATUS = {
    # LEGAL - Target species for commercial tuna fishing
    "Albacore": "legal",
    "Bigeye tuna": "legal",
    "Yellowfin tuna": "legal",
    "Skipjack tuna": "legal",
    "Swordfish": "legal",  # Legal with permits in most regions

    # LEGAL - Other commercially valuable species
    "Mahi mahi": "legal",
    "Wahoo": "legal",

    # BYCATCH - Release required, not target species
    "Shark": "bycatch",  # Most shark species require release
    "Thresher shark": "bycatch",
    "Blue marlin": "bycatch",  # Often catch-and-release in commercial
    "Black marlin": "bycatch",
    "Striped marlin": "bycatch",
    "Indo Pacific sailfish": "bycatch",
    "Shortbill spearfish": "bycatch",
    "Opah": "bycatch",  # Often incidental, sometimes kept
    "Oilfish": "bycatch",

    # PROTECTED - Immediate release required, often endangered
    "Pelagic stingray": "protected",  # Protected in many jurisdictions
    "Mola mola": "protected",  # Ocean sunfish - protected in many areas

    # OTHER - Various handling
    "Great barracuda": "bycatch",
    "Long snouted lancetfish": "bycatch",
    "Sickle pomfret": "bycatch",
    "Pomfret": "bycatch",
    "Rainbow runner": "legal",  # Edible, sometimes kept
    "Snake mackerel": "bycatch",
    "Roudie scolar": "bycatch",

    # UNKNOWN - Needs identification
    "Unknown": "unknown",
}


def main():
    print("=" * 70)
    print("REGULATORY STATUS ANALYSIS FOR CATCHLOG POC")
    print("=" * 70)

    df = pd.read_csv(LABELS_FILE)
    fish_df = df[~df["label_l2"].isin(["HUMAN", "NoF"])]

    # Get counts per species
    species_counts = fish_df["label_l1"].value_counts().to_dict()

    # Group by regulatory status
    status_groups = {"legal": [], "bycatch": [], "protected": [], "unknown": []}

    for species, count in species_counts.items():
        status = REGULATORY_STATUS.get(species, "unknown")
        status_groups[status].append((species, count))

    # Sort each group by count
    for status in status_groups:
        status_groups[status].sort(key=lambda x: x[1], reverse=True)

    print("\n" + "=" * 70)
    print("SPECIES BY REGULATORY STATUS")
    print("=" * 70)

    for status, species_list in status_groups.items():
        total = sum(count for _, count in species_list)
        print(f"\n{'🟢' if status == 'legal' else '🟡' if status == 'bycatch' else '🔴' if status == 'protected' else '⚪'} {status.upper()} ({total:,} samples)")
        print("-" * 50)
        for species, count in species_list:
            print(f"  {species:<30} {count:>6,}")

    # Recommended POC species selection
    print("\n" + "=" * 70)
    print("RECOMMENDED SPECIES FOR POC")
    print("=" * 70)

    # Select top species from each category with minimum samples
    MIN_SAMPLES = 30  # Need at least this many for fine-tuning

    poc_species = {
        "legal": [],
        "bycatch": [],
        "protected": [],
    }

    # Legal: Top 4 tuna + mahi
    legal_targets = ["Albacore", "Yellowfin tuna", "Bigeye tuna", "Mahi mahi", "Skipjack tuna"]
    for species in legal_targets:
        if species in species_counts and species_counts[species] >= MIN_SAMPLES:
            poc_species["legal"].append((species, species_counts[species]))

    # Bycatch: Species with enough samples
    bycatch_targets = ["Shark", "Opah", "Oilfish", "Blue marlin", "Striped marlin"]
    for species in bycatch_targets:
        if species in species_counts and species_counts[species] >= MIN_SAMPLES:
            poc_species["bycatch"].append((species, species_counts[species]))

    # Protected: What we have
    protected_targets = ["Pelagic stingray", "Mola mola"]
    for species in protected_targets:
        if species in species_counts:
            poc_species["protected"].append((species, species_counts[species]))

    print("\n📋 TIER 1: MINIMUM VIABLE POC (5 species)")
    print("-" * 50)
    tier1 = [
        ("Albacore", species_counts.get("Albacore", 0), "legal"),
        ("Yellowfin tuna", species_counts.get("Yellowfin tuna", 0), "legal"),
        ("Shark", species_counts.get("Shark", 0), "bycatch"),
        ("Pelagic stingray", species_counts.get("Pelagic stingray", 0), "protected"),
        ("Unknown", species_counts.get("Unknown", 0), "unknown"),
    ]
    total_tier1 = 0
    for species, count, status in tier1:
        emoji = "🟢" if status == "legal" else "🟡" if status == "bycatch" else "🔴" if status == "protected" else "⚪"
        print(f"  {emoji} {species:<25} {count:>6,} ({status})")
        total_tier1 += count
    print(f"  {'Total:':<27} {total_tier1:>6,}")

    print("\n📋 TIER 2: FULL POC (10 species)")
    print("-" * 50)
    tier2 = [
        # Legal
        ("Albacore", species_counts.get("Albacore", 0), "legal"),
        ("Yellowfin tuna", species_counts.get("Yellowfin tuna", 0), "legal"),
        ("Bigeye tuna", species_counts.get("Bigeye tuna", 0), "legal"),
        ("Mahi mahi", species_counts.get("Mahi mahi", 0), "legal"),
        ("Skipjack tuna", species_counts.get("Skipjack tuna", 0), "legal"),
        # Bycatch
        ("Shark", species_counts.get("Shark", 0), "bycatch"),
        ("Opah", species_counts.get("Opah", 0), "bycatch"),
        ("Blue marlin", species_counts.get("Blue marlin", 0), "bycatch"),
        # Protected
        ("Pelagic stingray", species_counts.get("Pelagic stingray", 0), "protected"),
        # Unknown
        ("Unknown", species_counts.get("Unknown", 0), "unknown"),
    ]
    total_tier2 = 0
    for species, count, status in tier2:
        emoji = "🟢" if status == "legal" else "🟡" if status == "bycatch" else "🔴" if status == "protected" else "⚪"
        print(f"  {emoji} {species:<25} {count:>6,} ({status})")
        total_tier2 += count
    print(f"  {'Total:':<27} {total_tier2:>6,}")

    # Fine-tuning data recommendations
    print("\n" + "=" * 70)
    print("FINE-TUNING DATA RECOMMENDATIONS")
    print("=" * 70)

    print("\n🎯 OPTION A: Balanced (equal samples per class)")
    print("-" * 50)
    balanced_per_class = 500
    print(f"  Target: {balanced_per_class} samples per species")
    balanced_total = 0
    for species, count, status in tier2:
        samples = min(count, balanced_per_class)
        balanced_total += samples
        print(f"  {species:<25} {samples:>4} samples")
    print(f"  {'TOTAL:':<25} {balanced_total:>4} samples")

    print("\n🎯 OPTION B: Weighted by importance")
    print("-" * 50)
    print("  Legal species: 800 each (demo main flow)")
    print("  Bycatch: 400 each (less frequent)")
    print("  Protected: ALL available (critical, rare)")
    print("  Unknown: 200 (edge case)")
    weighted_total = 0
    for species, count, status in tier2:
        if status == "legal":
            samples = min(count, 800)
        elif status == "bycatch":
            samples = min(count, 400)
        elif status == "protected":
            samples = count  # Take all
        else:
            samples = min(count, 200)
        weighted_total += samples
        print(f"  {species:<25} {samples:>4} samples")
    print(f"  {'TOTAL:':<25} {weighted_total:>4} samples")

    print("\n🎯 OPTION C: Minimal POC (fastest to train)")
    print("-" * 50)
    print("  5 species, 200 samples each max")
    minimal_total = 0
    for species, count, status in tier1:
        samples = min(count, 200)
        minimal_total += samples
        print(f"  {species:<25} {samples:>4} samples")
    print(f"  {'TOTAL:':<25} {minimal_total:>4} samples")

    # Export recommended species config
    output = {
        "tier1_species": [
            {"name": "Albacore", "display": "Albacore Tuna", "status": "legal", "code": "ALB"},
            {"name": "Yellowfin tuna", "display": "Yellowfin Tuna", "status": "legal", "code": "YFT"},
            {"name": "Shark", "display": "Shark", "status": "bycatch", "code": "SHARK"},
            {"name": "Pelagic stingray", "display": "Pelagic Stingray", "status": "protected", "code": "PLS"},
            {"name": "Unknown", "display": "Unknown Species", "status": "unknown", "code": "UNK"},
        ],
        "tier2_species": [
            {"name": "Albacore", "display": "Albacore Tuna", "status": "legal", "code": "ALB"},
            {"name": "Yellowfin tuna", "display": "Yellowfin Tuna", "status": "legal", "code": "YFT"},
            {"name": "Bigeye tuna", "display": "Bigeye Tuna", "status": "legal", "code": "BET"},
            {"name": "Mahi mahi", "display": "Mahi-Mahi", "status": "legal", "code": "DOL"},
            {"name": "Skipjack tuna", "display": "Skipjack Tuna", "status": "legal", "code": "SKJ"},
            {"name": "Shark", "display": "Shark", "status": "bycatch", "code": "SHARK"},
            {"name": "Opah", "display": "Opah (Moonfish)", "status": "bycatch", "code": "LAG"},
            {"name": "Blue marlin", "display": "Blue Marlin", "status": "bycatch", "code": "BILL"},
            {"name": "Pelagic stingray", "display": "Pelagic Stingray", "status": "protected", "code": "PLS"},
            {"name": "Unknown", "display": "Unknown Species", "status": "unknown", "code": "UNK"},
        ],
    }

    with open("poc_species_config.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\n✅ Exported poc_species_config.json")

    # Print protected species detail
    print("\n" + "=" * 70)
    print("PROTECTED SPECIES DEEP DIVE")
    print("=" * 70)

    protected_in_data = fish_df[fish_df["label_l1"].isin(["Pelagic stingray", "Mola mola"])]
    print(f"\nTotal protected species samples: {len(protected_in_data)}")
    print(f"  Pelagic stingray: {len(fish_df[fish_df['label_l1'] == 'Pelagic stingray'])}")
    print(f"  Mola mola (Ocean sunfish): {len(fish_df[fish_df['label_l1'] == 'Mola mola'])}")

    # Check unique images for protected
    protected_images = protected_in_data["img_id"].unique()
    print(f"\nUnique images with protected species: {len(protected_images)}")

    # Sample image IDs for verification
    print("\nSample protected species image IDs:")
    for species in ["Pelagic stingray", "Mola mola"]:
        sample_ids = fish_df[fish_df["label_l1"] == species]["img_id"].head(3).tolist()
        print(f"  {species}: {sample_ids}")


if __name__ == "__main__":
    main()
