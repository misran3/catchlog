"""
CatchLog - Full training script (3 epochs)
Run train_short.py first to verify the pipeline works.
"""

import os
import re
import json
import random
import shutil
import torch
from pathlib import Path
from collections import defaultdict, Counter
from PIL import Image
from tqdm import tqdm
from datasets import load_dataset
from transformers import (
    PaliGemmaProcessor,
    PaliGemmaForConditionalGeneration,
    BitsAndBytesConfig,
    Trainer,
    TrainingArguments,
)
from peft import get_peft_model, LoraConfig

# ── paths ──
IMAGES_DIR = "data/images"
LABELS_CSV = "data/labels/foid_labels_bbox_v012.csv"
OUTPUT_DIR = "output"
ADAPTER_DIR = os.path.join(OUTPUT_DIR, "catchlog-lora-adapter")
PROCESSED_DIR = os.path.join(OUTPUT_DIR, "processed")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# ── species ──
TARGET_SPECIES = {
    # Legal
    "Albacore":               {"name": "ALB",   "status": "legal"},
    "Yellowfin tuna":         {"name": "YFT",   "status": "legal"},
    "Bigeye tuna":            {"name": "BET",   "status": "legal"},
    "Skipjack tuna":          {"name": "SKJ",   "status": "legal"},
    "Mahi mahi":              {"name": "DOL",   "status": "legal"},
    "Swordfish":              {"name": "SWO",   "status": "legal"},
    "Wahoo":                  {"name": "WAH",   "status": "legal"},
    "Shortbill spearfish":    {"name": "SSF",   "status": "legal"},
    "Long snouted lancetfish": {"name": "LAF",  "status": "legal"},
    "Great barracuda":        {"name": "BAR",   "status": "legal"},
    "Sickle pomfret":         {"name": "SPF",   "status": "legal"},
    "Pomfret":                {"name": "POM",   "status": "legal"},
    "Rainbow runner":         {"name": "RRN",   "status": "legal"},
    "Snake mackerel":         {"name": "SNM",   "status": "legal"},
    "Roudie scolar":          {"name": "RSC",   "status": "legal"},
    # Bycatch
    "Shark":                  {"name": "SHK",   "status": "bycatch"},
    "Thresher shark":         {"name": "THR",   "status": "bycatch"},
    "Opah":                   {"name": "OPA",   "status": "bycatch"},
    "Oilfish":                {"name": "OIL",   "status": "bycatch"},
    "Mola mola":              {"name": "MOL",   "status": "bycatch"},
    # Protected
    "Pelagic stingray":       {"name": "PLS",   "status": "protected"},
    "Striped marlin":         {"name": "STM",   "status": "protected"},
    "Blue marlin":            {"name": "BUM",   "status": "protected"},
    "Black marlin":           {"name": "BKM",   "status": "protected"},
    "Indo Pacific sailfish":  {"name": "SAI",   "status": "protected"},
    # Unknown
    "Unknown":                {"name": "UNK",   "status": "unknown"},
    # Ignore (not fish, but useful for "nothing here" training)
    "No fish":                {"name": "NOF",   "status": "ignore"},
}

# ── training params ──
MAX_SAMPLES_PER_SPECIES = 600
VAL_SPLIT = 0.1
MODEL_ID = "google/paligemma2-3b-pt-224"
NUM_EPOCHS = 3
BATCH_SIZE = 16
GRADIENT_ACCUMULATION = 1
LEARNING_RATE = 2e-5
LORA_RANK = 8
MAX_NEW_TOKENS = 256


# ── helpers ──
def to_paligemma_locs(x_min, x_max, y_min, y_max, img_w, img_h):
    ly1 = min(1023, max(0, int((y_min / img_h) * 1023)))
    lx1 = min(1023, max(0, int((x_min / img_w) * 1023)))
    ly2 = min(1023, max(0, int((y_max / img_h) * 1023)))
    lx2 = min(1023, max(0, int((x_max / img_w) * 1023)))
    return f"<loc{ly1:04d}><loc{lx1:04d}><loc{ly2:04d}><loc{lx2:04d}>"


def run_inference(mdl, proc, image_path):
    image = Image.open(image_path).convert("RGB")
    inputs = proc(text="<image>detect fish", images=image, return_tensors="pt")
    inputs = {k: v.to(mdl.device) for k, v in inputs.items()}
    with torch.no_grad():
        output = mdl.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS)
    return proc.decode(output[0], skip_special_tokens=False)


def parse_detections(text):
    pattern = r"<loc(\d{4})><loc(\d{4})><loc(\d{4})><loc(\d{4})>\s*([^<;]+)"
    return [
        {"bbox": [int(x1)/1023, int(y1)/1023, int(x2)/1023, int(y2)/1023], "species": label.strip()}
        for y1, x1, y2, x2, label in re.findall(pattern, text)
    ]


# ══════════════════════════════════════════════════════════════
# 1. CUDA CHECK
# ══════════════════════════════════════════════════════════════
print(f"PyTorch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
else:
    print("NO GPU -- something is wrong")
    exit(1)


# ══════════════════════════════════════════════════════════════
# 2. DATA PREP
# ══════════════════════════════════════════════════════════════
import pandas as pd

df = pd.read_csv(LABELS_CSV)
print(f"\ntotal annotations: {len(df)}")

df_filtered = df[df["label_l1"].isin(TARGET_SPECIES.keys())].copy()

available_images = {}
for f in os.listdir(IMAGES_DIR):
    if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff")):
        img_id = os.path.splitext(f)[0]
        available_images[img_id] = os.path.join(IMAGES_DIR, f)

print(f"found {len(available_images)} images on disk")

df_filtered = df_filtered[df_filtered["img_id"].isin(available_images.keys())]
print(f"annotations with matching images: {len(df_filtered)}")

random.seed(42)

image_annotations = defaultdict(list)
for _, row in df_filtered.iterrows():
    image_annotations[row["img_id"]].append(row)

species_entries = defaultdict(list)
errors = 0

for img_id, annotations in tqdm(image_annotations.items(), desc="building dataset"):
    img_path = available_images[img_id]
    try:
        with Image.open(img_path) as img:
            img_w, img_h = img.size
    except Exception:
        errors += 1
        continue

    suffix_parts = []
    species_in_image = set()
    for ann in annotations:
        species_name = TARGET_SPECIES[ann["label_l1"]]["name"]
        locs = to_paligemma_locs(ann["x_min"], ann["x_max"], ann["y_min"], ann["y_max"], img_w, img_h)
        suffix_parts.append(f"{locs} {species_name}")
        species_in_image.add(ann["label_l1"])

    entry = {
        "image": img_path,
        "prefix": "detect fish",
        "suffix": " ; ".join(suffix_parts),
        "species": list(species_in_image),
    }
    for sp in species_in_image:
        species_entries[sp].append(entry)

# balance
balanced = {}
for sp, entries in species_entries.items():
    random.shuffle(entries)
    for entry in entries[:MAX_SAMPLES_PER_SPECIES]:
        balanced[entry["image"]] = entry

all_entries = list(balanced.values())
random.shuffle(all_entries)
print(f"total unique images after balancing: {len(all_entries)}")

# print distribution
sp_counts = Counter()
for e in all_entries:
    for sp in e["species"]:
        sp_counts[sp] += 1
print("\nbalanced distribution:")
for sp, c in sp_counts.most_common():
    print(f"  {sp}: {c}")

from sklearn.model_selection import train_test_split

primary_species = [e["species"][0] for e in all_entries]
try:
    train_entries, val_entries = train_test_split(
        all_entries, test_size=VAL_SPLIT, stratify=primary_species, random_state=42
    )
except ValueError:
    # Fallback if any class has too few samples for stratification
    split_idx = int(len(all_entries) * (1 - VAL_SPLIT))
    train_entries = all_entries[:split_idx]
    val_entries = all_entries[split_idx:]

train_path = os.path.join(PROCESSED_DIR, "train.jsonl")
val_path = os.path.join(PROCESSED_DIR, "val.jsonl")

for entries, path in [(train_entries, train_path), (val_entries, val_path)]:
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps({"image": e["image"], "prefix": e["prefix"], "suffix": e["suffix"]}) + "\n")

print(f"train: {len(train_entries)} | val: {len(val_entries)}")


# ══════════════════════════════════════════════════════════════
# 3. LOAD MODEL
# ══════════════════════════════════════════════════════════════
print("\nloading paligemma 2 3b with 4-bit quantization...")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
)

processor = PaliGemmaProcessor.from_pretrained(MODEL_ID)
model = PaliGemmaForConditionalGeneration.from_pretrained(
    MODEL_ID,
    quantization_config=bnb_config,
    device_map="auto",
)

for name, param in model.named_parameters():
    if "language_model" not in name:
        param.requires_grad = False

lora_config = LoraConfig(
    r=LORA_RANK,
    target_modules=["q_proj", "o_proj", "k_proj", "v_proj", "gate_proj", "up_proj", "down_proj"],
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()


# ══════════════════════════════════════════════════════════════
# 4. BASE MODEL TEST (before training)
# ══════════════════════════════════════════════════════════════
random.seed(99)
sample_img_ids = random.sample(list(image_annotations.keys()), min(5, len(image_annotations)))

print("\n" + "=" * 60)
print("BASE MODEL (before fine-tuning)")
print("=" * 60)

base_results = {}
for img_id in sample_img_ids:
    img_path = available_images[img_id]
    anns = image_annotations[img_id]
    ground_truth = [TARGET_SPECIES[a["label_l1"]]["name"] for a in anns]
    raw_output = run_inference(model, processor, img_path)
    detections = parse_detections(raw_output)
    base_results[img_id] = raw_output

    print(f"\n  {os.path.basename(img_path)}")
    print(f"    truth:  {ground_truth}")
    print(f"    output: {raw_output[:150]}")
    if detections:
        print(f"    parsed: {[d['species'] for d in detections]}")
    else:
        print(f"    parsed: (no loc tokens)")


# ══════════════════════════════════════════════════════════════
# 5. DATASET + COLLATE
# ══════════════════════════════════════════════════════════════
train_dataset = load_dataset("json", data_files=train_path, split="train")
val_dataset = load_dataset("json", data_files=val_path, split="train")

DTYPE = model.dtype

def collate_fn(examples):
    texts = []
    labels = []
    images = []
    for ex in examples:
        texts.append(f"<image>{ex['prefix']}")
        labels.append(ex["suffix"])
        try:
            images.append(Image.open(ex["image"]).convert("RGB"))
        except Exception:
            images.append(Image.new("RGB", (224, 224), color="black"))
    tokens = processor(text=texts, images=images, suffix=labels, return_tensors="pt", padding="longest")
    tokens = tokens.to(DTYPE)
    return tokens


# ══════════════════════════════════════════════════════════════
# 6. FULL TRAINING (3 epochs)
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("FULL TRAINING")
print(f"epochs: {NUM_EPOCHS}")
print(f"batch: {BATCH_SIZE} x {GRADIENT_ACCUMULATION} = {BATCH_SIZE * GRADIENT_ACCUMULATION} effective")
print(f"lr: {LEARNING_RATE}")
print(f"train: {len(train_dataset)} | val: {len(val_dataset)}")
print("=" * 60)

training_args = TrainingArguments(
    output_dir=os.path.join(OUTPUT_DIR, "checkpoints"),
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUMULATION,
    learning_rate=LEARNING_RATE,
    warmup_steps=50,
    bf16=True,
    logging_steps=20,
    eval_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=2,
    remove_unused_columns=False,
    dataloader_pin_memory=False,
    report_to="none",
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
)

trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=collate_fn,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
)

trainer.train()

print("\n" + "=" * 60)
print("TRAINING DONE")
print("=" * 60)


# ══════════════════════════════════════════════════════════════
# 7. VALIDATION (post-training)
# ══════════════════════════════════════════════════════════════
print("\nPOST-TRAINING validation on val set")
print("=" * 50)

correct = 0
total = min(10, len(val_dataset))

for i in range(total):
    entry = val_dataset[i]
    result = run_inference(model, processor, entry["image"])
    detections = parse_detections(result)

    expected = set()
    for sp in TARGET_SPECIES.values():
        if sp["name"] in entry["suffix"]:
            expected.add(sp["name"])

    predicted = set(d["species"] for d in detections)
    match = bool(expected & predicted)
    if match:
        correct += 1

    print(f"\n  image {i+1}: {os.path.basename(entry['image'])}")
    print(f"    expected:  {expected}")
    print(f"    predicted: {predicted}")
    print(f"    {'MATCH' if match else 'MISS'}")

print(f"\naccuracy: {correct}/{total} ({100*correct/total:.0f}%)")

# before/after comparison
print("\n" + "=" * 60)
print("BEFORE vs AFTER fine-tuning")
print("=" * 60)

for img_id in sample_img_ids:
    img_path = available_images[img_id]
    anns = image_annotations[img_id]
    ground_truth = [TARGET_SPECIES[a["label_l1"]]["name"] for a in anns]
    after_output = run_inference(model, processor, img_path)
    after_dets = parse_detections(after_output)

    print(f"\n  {os.path.basename(img_path)}")
    print(f"    truth:  {ground_truth}")
    print(f"    BEFORE: {base_results[img_id][:120]}")
    print(f"    AFTER:  {after_output[:120]}")
    if after_dets:
        print(f"    parsed: {[d['species'] for d in after_dets]}")


# ══════════════════════════════════════════════════════════════
# 8. SAVE ADAPTER
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print(f"saving adapter to {ADAPTER_DIR}...")

os.makedirs(ADAPTER_DIR, exist_ok=True)
model.save_pretrained(ADAPTER_DIR)
processor.save_pretrained(ADAPTER_DIR)

total_size = sum(f.stat().st_size for f in Path(ADAPTER_DIR).rglob("*") if f.is_file())
print(f"adapter size: {total_size / 1e6:.1f} MB")

shutil.make_archive(os.path.join(OUTPUT_DIR, "catchlog-lora-adapter"), "zip", ADAPTER_DIR)
print(f"zipped to: {OUTPUT_DIR}/catchlog-lora-adapter.zip")
print("\nALL DONE")
print("=" * 60)
