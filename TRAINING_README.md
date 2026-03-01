# CatchLog Training Guide

## Quick Start

### 1. SSH to VM

```bash
ssh hackathon@<VM_IP>
cd /home/hackathon/catchlog
```

### 2. Verify Data

```bash
ls data/images | wc -l        # Should show ~35k images
ls data/labels/               # Should have foid_labels_bbox_v012.csv
```

### 3. Run Smoke Test (2-3 min)

```bash
python train_short.py
```

**Expected output:**
- CUDA check passes
- Data prep completes (~3k unique images after balancing)
- Model loads with QLoRA
- 10 training steps complete
- Loss decreases

### 4. Run Full Training (~1-2 hours)

```bash
python train_full.py
```

**Expected output:**
- 3 epochs of training
- Validation after each epoch
- Before/after comparison
- Adapter saved to `output/catchlog-lora-adapter/`
- Zip created at `output/catchlog-lora-adapter.zip`

---

## Download Trained Model to Local Mac

### Option A: SCP (Recommended)

```bash
# From your local machine
scp -r hackathon@<VM_IP>:/home/hackathon/catchlog/output/catchlog-lora-adapter.zip ~/Downloads/

# Unzip to backend
cd /path/to/catchlog/backend
mkdir -p models
unzip ~/Downloads/catchlog-lora-adapter.zip -d models/catchlog-lora-adapter
```

### Option B: Via Google Drive

```bash
# On VM - upload to Drive
pip install gdown
# Upload manually or use gdrive CLI

# On local - download
gdown <DRIVE_FILE_ID> -O ~/Downloads/catchlog-lora-adapter.zip
```

### Verify Download

```bash
ls backend/models/catchlog-lora-adapter/
# Should contain:
# - adapter_config.json
# - adapter_model.safetensors
# - (possibly) tokenizer files
```

---

## Run Model Locally (Mac M1/M2)

### 1. Install Dependencies

```bash
cd backend
pip install torch torchvision
pip install transformers>=4.47.0 peft accelerate
```

### 2. Quick Test

```python
# test_local_model.py
from transformers import PaliGemmaProcessor, PaliGemmaForConditionalGeneration
from peft import PeftModel
from PIL import Image
import torch

# Load
processor = PaliGemmaProcessor.from_pretrained("google/paligemma2-3b-pt-224")
model = PaliGemmaForConditionalGeneration.from_pretrained(
    "google/paligemma2-3b-pt-224",
    torch_dtype=torch.float16,
    device_map="mps",
)
model = PeftModel.from_pretrained(model, "models/catchlog-lora-adapter")
model.eval()

# Test
image = Image.open("test_image.jpg").convert("RGB")
inputs = processor(text="<image>detect fish", images=image, return_tensors="pt")
inputs = {k: v.to("mps", dtype=torch.float16) for k, v in inputs.items()}

with torch.no_grad():
    output = model.generate(**inputs, max_new_tokens=256)

print(processor.decode(output[0], skip_special_tokens=False))
```

### 3. Expected Output Format

```
<loc0340><loc0156><loc0782><loc0534> ALB ; <loc0100><loc0200><loc0400><loc0500> SHK
```

- `<loc####>` = normalized bounding box coordinates (0-1023)
- Order: `y1, x1, y2, x2`
- Species codes: ALB, YFT, BET, SHK, PLS, etc.

---

## Training Config Reference

| Parameter | Value |
|-----------|-------|
| Base Model | `google/paligemma2-3b-pt-224` |
| Quantization | 4-bit NF4 |
| LoRA Rank | 8 |
| LoRA Targets | q, k, v, o, gate, up, down proj |
| Batch Size | 16 |
| Epochs | 3 |
| Learning Rate | 2e-5 |
| Max Samples/Species | 600 |

---

## Species Codes (Model Output)

| Code | Species | Status |
|------|---------|--------|
| ALB | Albacore Tuna | legal |
| YFT | Yellowfin Tuna | legal |
| BET | Bigeye Tuna | legal |
| SKJ | Skipjack Tuna | legal |
| DOL | Mahi-Mahi | legal |
| SWO | Swordfish | legal |
| SHK | Shark | bycatch |
| THR | Thresher Shark | bycatch |
| OPA | Opah | bycatch |
| OIL | Oilfish | bycatch |
| MOL | Mola Mola | bycatch |
| PLS | Pelagic Stingray | protected |
| STM | Striped Marlin | protected |
| BUM | Blue Marlin | protected |
| BKM | Black Marlin | protected |
| SAI | Indo Pacific Sailfish | protected |
| UNK | Unknown | unknown |
| NOF | No Fish | ignore |

---

## Troubleshooting

### OOM on VM
```bash
# Reduce batch size in train_full.py
BATCH_SIZE = 8  # was 16
```

### Slow Training
```bash
# Check GPU utilization
nvidia-smi -l 1
```

### Model Not Learning
- Check loss is decreasing in logs
- Verify data paths are correct
- Run smoke test first

### Local Mac OOM
```python
# Use CPU fallback (slower but works)
device_map="cpu"
torch_dtype=torch.float32
```
