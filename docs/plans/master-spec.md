# CatchLog Master Specification

**On-Device Fishing Compliance Agent**

*"Every fish identified. Every catch logged. Zero cloud. Zero connectivity required."*

Google DeepMind x InstaLILY On-Device AI Hackathon | February 2026 | 8 Hours

---

## 1. Product Overview

### What is CatchLog?

CatchLog is an on-device AI agent that monitors fishing vessel catch via deck cameras, identifies species in real-time, and enforces regulatory compliance — all without internet connectivity.

### The Problem

Commercial fishing vessels carry electronic monitoring cameras for regulatory compliance. Today, this footage is reviewed **manually by humans on land** — taking up to 3 months to review one week of footage. Protected species encounters go undetected until it's too late.

### The Solution

CatchLog processes camera feeds **on the vessel in real-time**:
- Identifies fish species as they come aboard
- Classifies each catch: legal / bycatch / protected
- Logs every detection to local database
- Triggers immediate voice alerts for protected species
- Generates compliance summary automatically

### User Personas

| User | Need | CatchLog Delivers |
|------|------|-------------------|
| **Fishermen** (on vessel) | Know immediately when to release a catch | Real-time voice alerts |
| **Organizations** (vessel operators) | Prove compliance to regulators | Automated audit log + compliance summary |

### Why On-Device is Non-Negotiable

| Constraint | Why Cloud Fails |
|------------|-----------------|
| **Zero connectivity** | Vessels operate 200+ miles offshore for days/weeks |
| **Data volume** | Cameras generate TB of video — cannot stream |
| **Commercial sensitivity** | Catch data = competitive advantage |
| **Latency** | Protected species alerts need sub-second response |

### Hackathon Requirements Coverage

| Requirement | How CatchLog Addresses It |
|-------------|---------------------------|
| Fine-tuned on-device model | PaliGemma 2 3B + LoRA on Fishnet dataset |
| Agentic behavior | Autonomous detect → classify → log → alert loop |
| Visual input | Video frames processed in real-time |
| Genuine on-device reason | No internet at sea, latency-critical, sensitive data |
| Voice (bonus) | ElevenLabs pre-generated alerts for protected species |

---

## 2. System Architecture

### High-Level Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Video Source   │────▶│  Frame Extractor │────▶│  PaliGemma 2 3B │
│ (Fishnet images)│     │   (OpenCV, 1fps) │     │  (Fine-tuned)   │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Dashboard     │◀────│   HTTP Polling   │◀────│  Agent Engine   │
│   (Next.js)     │     │   (every 1-2s)   │     │ (Python + SQLite)│
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                                                 ┌─────────────────┐
                                                 │  Voice Alerts   │
                                                 │ (Pre-gen audio) │
                                                 └─────────────────┘
```

### Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Vision Model** | PaliGemma 2 3B + LoRA | Species detection + bounding boxes |
| **Fine-tuning** | QLoRA via HuggingFace PEFT | Train on Colab Pro / InstaLILY VM |
| **Inference** | PyTorch + MPS (M2 Mac) | Local inference ~1-3 sec/frame |
| **Video Processing** | OpenCV | Frame extraction, bbox overlay |
| **Agent Logic** | Python | Regulatory checks, decision loop |
| **Database** | SQLite | Catch log persistence |
| **API Server** | FastAPI | Serves detections to dashboard |
| **Dashboard** | Next.js 14 + Tailwind | Simple POC UI |
| **Voice Alerts** | ElevenLabs (pre-generated) | Audio files played via `afplay` |

### Key Design Decisions

1. **Polling over WebSocket** — Simpler, fewer failure modes for a POC
2. **SQLite over Postgres** — Zero setup, single file, on-device story
3. **Pre-generated audio** — No API latency during demo
4. **1 FPS processing** — Matches real-world pace, manageable on M2

### Project Structure

```
catchlog/
├── model/
│   ├── data_prep.py                # Fishnet → PaliGemma JSONL converter
│   ├── finetune_notebook.ipynb     # Colab Pro fine-tuning notebook
│   └── catchlog-lora-adapter/      # Downloaded LoRA weights (~45MB)
├── backend/
│   ├── main.py                     # FastAPI server + orchestration
│   ├── inference.py                # PaliGemma model loading + inference
│   ├── video_processor.py          # OpenCV frame extraction + detection loop
│   ├── agent.py                    # CatchLogAgent: decision engine + logging
│   ├── regulations.json            # Species regulatory database
│   └── catch_log.db                # SQLite database (auto-created)
├── frontend/
│   ├── app/
│   │   ├── page.tsx                # Main dashboard page
│   │   └── components/
│   │       ├── VideoFeed.tsx       # Live video with bounding box overlays
│   │       ├── CatchCounter.tsx    # Running species count table
│   │       └── AlertFeed.tsx       # Scrolling event log with alerts
│   └── package.json
├── assets/
│   └── audio/                      # Pre-generated ElevenLabs alerts
│       ├── alert_info.mp3
│       ├── alert_warning.mp3
│       └── alert_critical.mp3
├── demo-images/                    # Curated Fishnet images for demo
├── requirements.txt
└── README.md
```

---

## 3. Agent Behavior & Decision Logic

### The Agentic Loop

Every 1-2 seconds, the agent runs this autonomous cycle:

```
┌──────────────────────────────────────────────────────────────┐
│                    AGENT DECISION LOOP                       │
├──────────────────────────────────────────────────────────────┤
│  1. PERCEIVE   → Extract frame → Run PaliGemma inference     │
│  2. DETECT     → Parse bounding boxes + species labels       │
│  3. CLASSIFY   → Check species against regulations DB        │
│  4. DECIDE     → Determine action: log / warn / critical     │
│  5. LOG        → Write to SQLite: timestamp, species, status │
│  6. ALERT      → If protected/bycatch → play voice alert     │
│  7. BROADCAST  → Update API state for dashboard polling      │
└──────────────────────────────────────────────────────────────┘
```

### Regulatory Classification

| Status | Species | Agent Action | Alert Level |
|--------|---------|--------------|-------------|
| `legal` | Albacore, Bigeye, Mahi-Mahi | Log catch, increment count | None |
| `bycatch` | Blue Shark | Log + warning alert | Warning (yellow) |
| `protected` | Sea Turtle* | Log + critical alert + voice | Critical (red) |
| `unknown` | Unrecognized | Flag for manual review | Info (gray) |

*Or substitute based on Fishnet dataset availability

### Regulations Database Schema

```json
{
  "Albacore Tuna": {
    "status": "legal",
    "action": "log",
    "alert_level": "none"
  },
  "Bigeye Tuna": {
    "status": "legal",
    "action": "log",
    "alert_level": "none"
  },
  "Mahi-Mahi": {
    "status": "legal",
    "action": "log",
    "alert_level": "none"
  },
  "Blue Shark": {
    "status": "bycatch",
    "action": "alert_release",
    "alert_level": "warning",
    "message": "Bycatch detected. Blue Shark. Release required."
  },
  "Sea Turtle": {
    "status": "protected",
    "action": "critical_alert",
    "alert_level": "critical",
    "message": "ALERT. Protected species detected. Immediate release required."
  },
  "Unknown": {
    "status": "unidentified",
    "action": "flag_review",
    "alert_level": "info",
    "message": "Unidentified species. Flagged for manual review."
  }
}
```

### Voice Alert Scripts (Pre-generated via ElevenLabs)

| Alert Level | Audio Script | File |
|-------------|--------------|------|
| **Info** | "Catch logged. Bigeye Tuna. Count updated." | `alert_info.mp3` |
| **Warning** | "Bycatch detected. Blue Shark. Release required." | `alert_warning.mp3` |
| **Critical** | "ALERT. Protected species detected. Immediate release required." | `alert_critical.mp3` |

### What Makes This "Agentic"

- **Autonomous**: No human triggers the loop — it runs continuously
- **Goal-directed**: Enforcing fishing regulations is the objective
- **Decision-making**: Agent chooses action based on species classification
- **Side effects**: Logs to database, triggers alerts, updates UI

---

## 4. Dashboard UI (POC)

### Layout — Single Page, 3 Panels

```
┌─────────────────────────────────────────────────────────────────┐
│                        CATCHLOG DASHBOARD                       │
├───────────────────────────────────┬─────────────────────────────┤
│                                   │                             │
│         LIVE VIDEO FEED           │       CATCH COUNTER         │
│                                   │                             │
│   [Image with bounding boxes]     │   Species        Count      │
│                                   │   ─────────────────────     │
│   ● Green box = Legal             │   Albacore Tuna    12       │
│   ● Yellow box = Bycatch          │   Bigeye Tuna       8       │
│   ● Red box = Protected           │   Mahi-Mahi         5       │
│                                   │   Blue Shark        1 ⚠️    │
│                                   │                             │
├───────────────────────────────────┴─────────────────────────────┤
│                         ALERT FEED                              │
│                                                                 │
│  14:23:05  ● Albacore Tuna detected (Legal)                     │
│  14:23:08  ● Bigeye Tuna detected (Legal) — Count: 8            │
│  14:23:12  ⚠️ BYCATCH: Blue Shark — Release required            │
│  14:23:15  🔴 CRITICAL: Protected species — Immediate release   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Compliance Summary (In Dashboard)

```
┌─────────────────────────────────────┐
│         TRIP COMPLIANCE             │
├─────────────────────────────────────┤
│  Total Catch:              26       │
│  Legal:                    24       │
│  Bycatch (Released):        1       │
│  Protected (Released):      1       │
│                                     │
│  Status:    ✓ COMPLIANT             │
└─────────────────────────────────────┘
```

### Mock Release Feature

For demo purposes, a "Simulate Release" button (or `R` key) marks the last protected/bycatch species as released:

```
Before: "Sea Turtle | PROTECTED | ALERT SENT"
After:  "Sea Turtle | PROTECTED | RELEASED"

Compliance: Protected Species Encounters: 1, Released: 1 → COMPLIANT
```

### Data Flow

```
Backend (FastAPI)              Frontend (Next.js)
      │                              │
      │  GET /api/state              │
      │◀─────────────────────────────│  Poll every 1-2 sec
      │                              │
      │  {                           │
      │    frame_base64: "...",      │
      │    detections: [...],        │
      │    counts: {...},            │
      │    alerts: [...],            │
      │    compliance: {...}         │
      │  }                           │
      │─────────────────────────────▶│
      │                              │  Update UI
```

### Tech Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Framework | Next.js 14 (App Router) | Fast setup, familiar |
| Styling | Tailwind CSS | Rapid prototyping |
| Polling | `setInterval` + `fetch` | Simpler than WebSocket for POC |
| Image display | Base64 in `<img>` tag | No file serving complexity |

### NOT Building

- PDF report export
- Historical data views
- User authentication
- Mobile responsiveness

---

## 5. Fine-tuning Pipeline

### Dataset: Fishnet Open Images

| Attribute | Value |
|-----------|-------|
| Source | fishnet.ai/download |
| Images | 143,818 |
| Bounding boxes | 549,209 |
| Species classes | 34 |
| License | Open source (The Nature Conservancy) |

### Target Species (Pending Verification in T1)

| Species | Code | Role in Demo |
|---------|------|--------------|
| Albacore Tuna | ALB | Legal catch |
| Bigeye Tuna | BET | Legal catch |
| Mahi-Mahi | DOL | Legal, visually distinct |
| Blue Shark | BSH | Bycatch trigger |
| Sea Turtle | TBD | Protected species (verify availability) |

### Data Prep → PaliGemma Format

**Input** (Fishnet CSV):
```
image_id, x, y, w, h, species_code
IMG_001, 120, 80, 200, 150, BET
```

**Output** (PaliGemma JSONL):
```json
{
  "image": "path/to/IMG_001.jpg",
  "prefix": "detect fish",
  "suffix": "<loc0123><loc0456><loc0789><loc0234> Bigeye Tuna"
}
```

Conversion: Normalize bbox coords to 0-1023 range for `<locXXXX>` tokens.

### Training Config (QLoRA)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Base model | `google/paligemma2-3b-pt-224` | 224px input, smaller = faster |
| Quantization | 4-bit NF4 | Fits in GPU memory |
| LoRA rank | 8 | Good balance speed/quality |
| LoRA targets | q, k, v, o, gate, up, down proj | Standard for language head |
| Epochs | 2-3 | ~20-30 min on A100 |
| Batch size | 4 | A100 can handle this |
| Learning rate | 2e-5 | Standard for LoRA |

### Training Environment

| Option | Hardware | Use For |
|--------|----------|---------|
| Colab Pro | A100 (40GB) | Primary training |
| InstaLILY VM | TBD GPU | Backup / parallel experiments |

### Output

- LoRA adapter: ~45MB
- Download to M2 Mac for local inference

### Before/After Comparison (For Judges)

| Model | Input | Output |
|-------|-------|--------|
| Base PaliGemma 2 3B | Fishnet image + "detect fish" | "fish" (generic) |
| Fine-tuned CatchLog | Same image + "detect fish" | "<loc...> Bigeye Tuna" (specific + bbox) |

This side-by-side is the "money shot" for proving fine-tuning value.

---

## 6. Task Breakdown

**Timeline**: 6 hours build + 2 hours buffer
**Team**: 2 generalists, flexible task pool

### Hour 1: Setup & Data Prep

| ID | Task | Est. | Dependencies | Output |
|----|------|------|--------------|--------|
| **T1** | Download Fishnet dataset, verify species availability | 30m | None | Species list confirmed |
| **T2** | Write `data_prep.py` — convert Fishnet → PaliGemma JSONL | 30m | T1 | `fishnet_train.jsonl` |
| **T3** | Set up project repo structure, install Python deps | 20m | None | Working dev environment |
| **T4** | Init Next.js app with Tailwind, basic layout scaffold | 20m | None | Empty 3-panel layout |
| **T5** | Generate ElevenLabs audio files (3 alerts) | 15m | None | `.mp3` files ready |

**Parallel**: T1 + T3 + T4 + T5 can start simultaneously.

### Hour 2: Fine-tuning & Mock Integration

| ID | Task | Est. | Dependencies | Output |
|----|------|------|--------------|--------|
| **T6** | Upload data to Drive/VM, start fine-tuning | 15m | T2 | Training running |
| **T7** | Write `regulations.json` (5 species) | 15m | T1 | Regulatory DB |
| **T8** | Write `agent.py` — CatchLogAgent class skeleton | 30m | T7 | Agent logic ready |
| **T9** | Build dashboard with mock data (hardcoded detections) | 40m | T4 | UI working with fake data |
| **T10** | Write FastAPI server skeleton (`main.py`) with `/api/state` | 20m | None | API endpoint ready |

**While training runs (~25 min)**: Work on T7, T8, T9, T10.

### Hour 3: Inference & Video Processing

| ID | Task | Est. | Dependencies | Output |
|----|------|------|--------------|--------|
| **T11** | Download LoRA adapter from Colab/VM | 10m | T6 complete | Adapter on Mac |
| **T12** | Write `inference.py` — load model + run on test image | 30m | T11 | Working inference |
| **T13** | Write `video_processor.py` — frame extraction + detection loop | 30m | T12 | Video → detections |
| **T14** | Integrate voice alerts into agent (play `.mp3` on trigger) | 20m | T5, T8 | Alerts working |

### Hour 4: Integration

| ID | Task | Est. | Dependencies | Output |
|----|------|------|--------------|--------|
| **T15** | Wire agent into video processor loop | 30m | T8, T13 | Full backend pipeline |
| **T16** | Connect FastAPI to agent state (real data) | 20m | T10, T15 | API serves real detections |
| **T17** | Connect dashboard to live API (replace mock data) | 30m | T9, T16 | UI shows real detections |
| **T18** | Draw bounding boxes on frames with OpenCV | 20m | T13 | Annotated frames |

### Hour 5: End-to-End Testing

| ID | Task | Est. | Dependencies | Output |
|----|------|------|--------------|--------|
| **T19** | Run full pipeline end-to-end, debug issues | 45m | T15, T17, T18 | Working demo |
| **T20** | Create before/after comparison (base vs fine-tuned) | 30m | T12 | Screenshot/slide ready |
| **T21** | Curate demo image sequence (10-15 Fishnet images) | 20m | T1, T19 | Demo footage ready |
| **T27** | Add mock release trigger + update compliance summary | 15m | T17 | Release demo working |

### Hour 6: Polish & Demo Prep

| ID | Task | Est. | Dependencies | Output |
|----|------|------|--------------|--------|
| **T22** | Fix remaining bugs from E2E testing | 30m | T19 | Stable system |
| **T23** | Demo rehearsal #1 — time it, note issues | 15m | T22 | Rehearsal notes |
| **T24** | Final UI polish (colors, alert styling) | 20m | T17 | Clean UI |
| **T25** | Prepare demo script / talking points | 15m | T23 | Demo ready |
| **T26** | Record backup demo video (screen capture) | 15m | T22 | Fallback if live fails |

### Hours 7-8: Buffer

Reserved for:
- Unexpected bugs
- Model performance issues
- Demo rehearsals
- Judge Q&A prep

### Critical Path

```
T1 ──▶ T2 ──▶ T6 ──▶ T11 ──▶ T12 ──▶ T13 ──▶ T15 ──▶ T19
                                       │
T7 ──▶ T8 ────────────────────────────┘
                                       │
T4 ──▶ T9 ──▶ T17 ────────────────────┘
```

**Critical path**: Data prep → Fine-tuning → Inference → Integration → E2E test

---

## 7. Scope Summary

### In Scope (MVP)

| Feature | Priority | Status |
|---------|----------|--------|
| PaliGemma 2 3B fine-tuned on Fishnet (5 species) | P0 | Must ship |
| Video frame processing at ~1 FPS | P0 | Must ship |
| Agent loop: detect → classify → log → alert | P0 | Must ship |
| SQLite catch logging with timestamps | P0 | Must ship |
| Voice alerts via ElevenLabs (pre-generated) | P0 | Must ship |
| Simple 3-panel dashboard (POC quality) | P0 | Must ship |
| Compliance summary in dashboard | P0 | Must ship |
| Mock release trigger for demo | P1 | Should ship |
| Before/after fine-tuning comparison | P1 | Should ship |
| Demo rehearsal + backup video | P1 | Should ship |

### Out of Scope (Explicitly Cut)

| Feature | Reason |
|---------|--------|
| PDF report export | Time sink, low demo value |
| Real-time ElevenLabs API calls | Pre-generated is simpler |
| WebSocket live updates | Polling is sufficient |
| Release detection via CV | No training data, rabbit hole |
| Size estimation from bboxes | Complex, error-prone |
| Multiple camera support | Overkill for POC |
| User authentication | Not relevant for demo |
| Mobile responsive UI | Desktop demo only |

### Stretch Goals (If Time Permits)

| Feature | Effort | Trigger |
|---------|--------|---------|
| Real-time ElevenLabs voice | 30m | Buffer time available in Hour 7 |
| Additional species (5→8) | 20m | Model accuracy is good |
| Animated alert banner | 15m | UI feels too static |

---

## 8. Dependencies & Setup

### Python Backend (M2 Mac)

```bash
pip install torch torchvision
pip install transformers>=4.47.0 peft accelerate
pip install fastapi uvicorn
pip install opencv-python-headless pillow
```

### Fine-tuning (Colab Pro / VM)

```bash
pip install bitsandbytes datasets
```

### Frontend

```bash
npx create-next-app@14 frontend --typescript --tailwind --app
cd frontend && npm install
```

### Voice Alerts

- ElevenLabs account (free tier sufficient)
- Generate 3 audio files via web UI or API
- Save to `assets/audio/`

---

## 9. Demo Narrative (Draft)

> **Hook (0:00)**
> "We built an AI fisheries officer that never sleeps, never misses a catch, and works in the middle of the Pacific with zero internet."

> **Problem (0:15)**
> "Commercial fishing vessels carry cameras for compliance. Today, all footage is reviewed manually — 3 months to review one week. Protected species caught? Nobody knows until it's too late."

> **Solution (0:45)**
> "CatchLog processes camera feeds in real-time, on the vessel, with no connectivity. It identifies species, checks regulations, and alerts fishermen in under 2 seconds."

> **Live Demo (1:00)**
> - Show detections appearing
> - Point out species differentiation (Albacore vs Bigeye)
> - Trigger protected species alert
> - Show mock release → compliance status updates

> **Fine-tuning Story (2:00)**
> - Before/after comparison
> - "Base model says 'fish'. Our model says 'Bigeye Tuna' with bounding box."

> **Why On-Device (2:30)**
> - No signal at sea
> - Too much video to upload
> - Catch data is commercially sensitive

> **Close (3:00)**
> - Show compliance summary
> - "This report used to take 3 months. CatchLog generates it in real-time."

---

*Document created: 2026-02-28*
*CatchLog — Google DeepMind x InstaLILY On-Device AI Hackathon*
