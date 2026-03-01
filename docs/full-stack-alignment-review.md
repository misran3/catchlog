# Full-Stack Alignment Review vs Master Spec

**Date:** 2026-02-28
**Reviewers:** Code Review Agents (Fine-tuning, Backend, Frontend)
**Reference:** `docs/plans/master-spec.md`

---

## Executive Summary

| Component | Alignment | Critical Issues |
|-----------|-----------|-----------------|
| Fine-tuning | 70% | BILL code collision, Pelagic Stingray status |
| Backend | 75% | Missing `video_processor.py`, no autonomous loop |
| Frontend | 85% | Missing polling mechanism |

**Overall Status:** Core architecture is sound. 4 critical blockers must be fixed before training/demo.

---

## Critical Blockers (Must Fix Before Demo)

### 1. BILL Code Collision (Fine-tuning)

**File:** `catchlog_finetune.ipynb` (cell-5)

**Problem:** 6 species with different regulatory statuses map to the same output code:

```python
# CURRENT (BAD)
"Swordfish":           {"name": "BILL", "status": "legal_regulated"},
"Striped marlin":      {"name": "BILL", "status": "protected"},
"Blue marlin":         {"name": "BILL", "status": "protected"},
"Black marlin":        {"name": "BILL", "status": "protected"},
"Shortbill spearfish": {"name": "BILL", "status": "legal_regulated"},
"Indo Pacific sailfish": {"name": "BILL", "status": "protected"},
```

**Impact:** Model outputs `BILL` → backend cannot distinguish legal Swordfish from protected Blue Marlin. Compliance decisions will be wrong.

**Fix:**
```python
"Swordfish":           {"name": "SWO", "status": "legal"},
"Striped marlin":      {"name": "STM", "status": "protected"},
"Blue marlin":         {"name": "BUM", "status": "protected"},
"Black marlin":        {"name": "BLM", "status": "protected"},
"Shortbill spearfish": {"name": "SSF", "status": "legal"},
"Indo Pacific sailfish": {"name": "SAI", "status": "protected"},
```

**Time:** 10 min

---

### 2. Pelagic Stingray Wrong Status (Fine-tuning)

**File:** `catchlog_finetune.ipynb` (cell-5)

**Problem:** Protected species substitute marked as `bycatch`:

```python
# CURRENT (BAD)
"Pelagic stingray": {"name": "PLS", "status": "bycatch"}
```

**Impact:** Demo's key protected species will trigger warning alert instead of critical alert.

**Fix:**
```python
"Pelagic stingray": {"name": "PLS", "status": "protected"}
```

**Time:** 1 min

---

### 3. No Polling Mechanism (Frontend)

**File:** `frontend/app/page.tsx`

**Problem:** Dashboard only fetches state on initial load and after uploads. No continuous polling.

**Spec Requirement:** "Poll every 1-2 sec" (Section 4)

**Impact:** Dashboard won't show live updates during demo.

**Fix:** Add to `page.tsx`:
```typescript
useEffect(() => {
  const intervalId = setInterval(refreshState, 1500);
  return () => clearInterval(intervalId);
}, [refreshState]);
```

**Time:** 5 min

---

### 4. No Autonomous Loop (Backend)

**Missing File:** `backend/video_processor.py`

**Problem:** System is request-driven (manual uploads), not autonomous.

**Spec Requirement:** "Every 1-2 seconds, the agent runs this autonomous cycle" (Section 3)

**Hackathon Requirement:** "Agentic behavior - your system decides and acts autonomously"

**Impact:** Violates core hackathon requirement #2.

**Fix Options:**
1. Create `video_processor.py` that processes demo images at 1 FPS
2. Add `/api/start-demo` endpoint that triggers autonomous processing
3. Implement WebSocket frame streaming

**Time:** 30-60 min

---

## High Priority Issues

| Issue | Component | File | Fix Time |
|-------|-----------|------|----------|
| Audio files are 11-byte stubs | Backend | `backend/audio/*.mp3` | 15 min |
| No rare class augmentation | Fine-tuning | Run `augment_rare_species.py` | 30 min |
| Human in training (104k samples) | Fine-tuning | Remove from TARGET_SPECIES | 1 min |
| No stratified train/val split | Fine-tuning | Use sklearn stratify | 5 min |
| No "R" key shortcut | Frontend | Add keypress listener | 5 min |
| Opah status mismatch | Fine-tuning | Change to bycatch | 1 min |

---

## What's Working Well

### Fine-tuning
- PaliGemma format correct (`<loc####>` tokens, y1-x1-y2-x2 order)
- QLoRA config exact match (4-bit NF4, rank 8, all 7 projection targets)
- Training params aligned (epochs 3, batch 4, LR 2e-5)
- Sample balancing (600 cap) implemented
- Multi-object handling with `;` separator

### Backend
- FastAPI `/api/state` endpoint returns correct schema
- SQLite schema with proper species/detections tables
- Regulatory status handling (4 statuses, compliance calculation)
- Excellent test coverage (15 tests across 2 files)
- Mock inference mode for deterministic demos
- Demo bboxes pre-defined for 20 images

### Frontend
- 3-panel responsive layout matches spec wireframe
- Bbox color coding (green=legal, yellow=bycatch, red=protected)
- Catch counter with status indicators and emoji markers
- Alert feed with timestamps and severity styling
- Compliance summary with COMPLIANT/ACTION_REQUIRED badge
- Species list aligned with backend
- Audio element for alert playback

---

## Cross-Component Species Alignment

| Species | Fine-tuning | Backend | Frontend | Status |
|---------|-------------|---------|----------|--------|
| Albacore Tuna | ALB (legal) | legal | legal | Aligned |
| Yellowfin Tuna | YFT (legal) | legal | legal | Aligned |
| Bigeye Tuna | BET (legal) | legal | legal | Aligned |
| Mahi-Mahi | DOL (legal) | legal | legal | Aligned |
| Shark | SHARK (bycatch) | bycatch | bycatch | Aligned |
| Opah | LAG (legal) | bycatch | bycatch | **Mismatch** |
| Pelagic Stingray | PLS (bycatch) | protected | protected | **Mismatch** |
| Unknown | OTH (unknown) | unknown | unknown | Aligned |

---

## Missing Files from Master Spec

| File | Spec Section | Purpose | Status |
|------|--------------|---------|--------|
| `backend/video_processor.py` | Section 2 | OpenCV frame extraction + detection loop | Not created |
| `backend/regulations.json` | Section 3 | Species regulatory database | Using Python constants |
| Real `*.mp3` audio files | Section 3 | ElevenLabs pre-generated alerts | Stubs only (11 bytes) |

---

## Priority Action Checklist

### Before Training (~45 min)

- [ ] Fix BILL code collision in `catchlog_finetune.ipynb` (10 min)
- [ ] Fix Pelagic Stingray status → `protected` (1 min)
- [ ] Fix Opah status → `bycatch` (1 min)
- [ ] Remove `Human` from TARGET_SPECIES (1 min)
- [ ] Add stratified train/val split with sklearn (5 min)
- [ ] Run data augmentation script for rare species (30 min)

### Before Demo (~1 hr)

- [ ] Add frontend polling mechanism (5 min)
- [ ] Generate real ElevenLabs audio files (15 min)
- [ ] Implement `video_processor.py` or demo auto-loop (30-45 min)
- [ ] Add "R" key shortcut for release (5 min)

---

## Detailed Component Reviews

### Fine-tuning Review

**QLoRA Configuration (Aligned):**

| Parameter | Spec | Implementation |
|-----------|------|----------------|
| Base model | `google/paligemma2-3b-pt-224` | Exact match |
| Quantization | 4-bit NF4 | Exact match |
| LoRA rank | 8 | Exact match |
| LoRA targets | q,k,v,o,gate,up,down proj | All 7 present |
| Epochs | 2-3 | 3 |
| Batch size | 4 | 4 |
| Learning rate | 2e-5 | 2e-5 |

**Data Format (Aligned):**
```python
# Correct implementation
def to_paligemma_locs(x_min, x_max, y_min, y_max, img_w, img_h):
    ly1 = min(1023, max(0, int((y_min / img_h) * 1023)))
    lx1 = min(1023, max(0, int((x_min / img_w) * 1023)))
    ly2 = min(1023, max(0, int((y_max / img_h) * 1023)))
    lx2 = min(1023, max(0, int((x_max / img_w) * 1023)))
    return f"<loc{ly1:04d}><loc{lx1:04d}><loc{ly2:04d}><loc{lx2:04d}>"
```

**Rare Class Problem:**

| Species | Samples | Cap | Risk |
|---------|---------|-----|------|
| Albacore | 33,943 | 600 | Capped (good) |
| Pelagic stingray | 40 | 600 | Only 40 used |
| Mola mola | 6 | 600 | Only 6 used |

Recommendation: Run augmentation to boost protected species from 40 → 160+.

---

### Backend Review

**Agent Loop (Partial):**

| Step | Spec | Implementation |
|------|------|----------------|
| PERCEIVE | Extract frame | Manual upload only |
| DETECT | Run inference | `run_inference()` |
| CLASSIFY | Check regulations | `get_species_by_name()` |
| DECIDE | Determine action | `STATUS_TO_ALERT` mapping |
| LOG | Write to SQLite | `log_detection()` |
| ALERT | Play voice | Audio URL returned |
| BROADCAST | Update API state | `_state` updated |

**Missing:** Autonomous loop that processes frames continuously.

**API Endpoint (Aligned):**
```python
@app.get("/api/state")
async def get_state() -> AppState:
    return agent.get_state()
```

---

### Frontend Review

**3-Panel Layout (Aligned):**
```
┌───────────────────────────────┬─────────────────────┐
│      Live Video Feed          │   Catch Counter     │
│      + Release Button         │   Compliance        │
├───────────────────────────────┴─────────────────────┤
│                    Alert Feed                       │
└─────────────────────────────────────────────────────┘
```

**Components (All Present):**
- `VideoFeed.tsx` - Frame display with species badge
- `CatchCounter.tsx` - Species counts with status dots
- `AlertFeed.tsx` - Timestamped alerts with severity styling
- `ComplianceSummary.tsx` - Stats + COMPLIANT/ACTION_REQUIRED badge
- `ReleaseButton.tsx` - Release trigger (missing "R" key shortcut)

---

## Justified Deviations from Spec

| Deviation | Reason | Assessment |
|-----------|--------|------------|
| Sea Turtle → Pelagic Stingray | Sea Turtle not in Fishnet dataset | Acceptable |
| Blue Shark → Shark | Dataset uses generic "Shark" class | Acceptable |
| Species count 5 → 28 | Richer demo with more variety | Acceptable (slower training) |
| `regulations.json` → Python constants | Simpler for hackathon | Acceptable |
| Bboxes drawn server-side | Simpler frontend | Acceptable for POC |

---

## Conclusion

The implementation is fundamentally sound with correct PaliGemma format, QLoRA configuration, and well-structured frontend/backend code. The **4 critical blockers** (BILL collision, Pelagic Stingray status, no polling, no autonomous loop) must be addressed for the demo to achieve its primary goal: demonstrating autonomous protected species detection and compliance alerts.

**Estimated total fix time:** ~2 hours

---

*Review generated by parallel code review agents*
