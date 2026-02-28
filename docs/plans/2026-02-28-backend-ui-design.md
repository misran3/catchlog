# CatchLog Backend + UI Design

**Date:** 2026-02-28
**Scope:** Backend API and Frontend Dashboard for POC demo
**Constraint:** Model fine-tuning handled separately by teammate

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CATCHLOG POC                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐    POST /api/upload    ┌─────────────────┐   │
│   │   Next.js    │ ──────────────────────▶│    FastAPI      │   │
│   │   Dashboard  │                        │    Backend      │   │
│   │              │    GET /api/state      │                 │   │
│   │  - Upload    │ ◀──────────────────────│  - Inference    │   │
│   │  - VideoFeed │                        │  - Agent        │   │
│   │  - Counter   │    POST /api/release   │  - SQLite       │   │
│   │  - Alerts    │ ──────────────────────▶│  - Audio files  │   │
│   └──────────────┘                        └─────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Tech stack:**
- Backend: FastAPI + SQLite (uv for package management)
- Frontend: Next.js 14 + Tailwind (bun for package management)

---

## API Contract

### `POST /api/upload`

Upload image, triggers processing, returns detection result.

**Request:** `multipart/form-data` with image file

**Response:**
```json
{
  "detection_id": 1,
  "timestamp": "2026-02-28T14:23:05Z",
  "species": "Bigeye Tuna",
  "status": "legal",
  "confidence": 0.92,
  "bbox": [120, 80, 320, 230],
  "alert_level": "none",
  "audio_url": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `detection_id` | int | Auto-increment ID from SQLite |
| `timestamp` | string | ISO 8601 format |
| `species` | string | Species name |
| `status` | string | `legal` \| `bycatch` \| `protected` \| `unknown` |
| `confidence` | float | 0.0-1.0 (mock: 0.75-0.98) |
| `bbox` | array | `[x1, y1, x2, y2]` pixel coordinates |
| `alert_level` | string | `none` \| `info` \| `warning` \| `critical` |
| `audio_url` | string? | Path to alert audio or null |

### `GET /api/state`

Get current dashboard state.

**Response:**
```json
{
  "last_detection": { },
  "frame_base64": "data:image/jpeg;base64,...",
  "counts": {
    "Albacore Tuna": 12,
    "Bigeye Tuna": 8,
    "Blue Shark": 1
  },
  "alerts": [
    {
      "timestamp": "2026-02-28T14:23:12Z",
      "message": "BYCATCH: Blue Shark — Release required",
      "level": "warning"
    }
  ],
  "compliance": {
    "total": 21,
    "legal": 20,
    "bycatch": 1,
    "protected": 0,
    "released": 1,
    "status": "COMPLIANT"
  }
}
```

### `POST /api/release`

Mark last unreleased bycatch/protected as released.

**Request:** Empty body

**Response:**
```json
{
  "released_id": 15,
  "species": "Blue Shark",
  "compliance_status": "COMPLIANT"
}
```

---

## Database Schema

Optimized for on-device storage (~18 bytes per detection).

```sql
-- Species lookup table (seeded on startup)
CREATE TABLE species (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    status INTEGER NOT NULL  -- 0=legal, 1=bycatch, 2=protected, 3=unknown
);

-- Detection audit log
CREATE TABLE detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL,           -- Unix timestamp
    species_id INTEGER NOT NULL,   -- FK to species
    released INTEGER DEFAULT 0,    -- 0=no, 1=yes
    FOREIGN KEY (species_id) REFERENCES species(id)
);
```

**Species seed data:**

| id | name | status |
|----|------|--------|
| 1 | Albacore Tuna | 0 (legal) |
| 2 | Bigeye Tuna | 0 (legal) |
| 3 | Mahi-Mahi | 0 (legal) |
| 4 | Blue Shark | 1 (bycatch) |
| 5 | Sea Turtle | 2 (protected) |
| 6 | Unknown | 3 (unknown) |

**In-memory only (not persisted):**
- Last frame with bbox overlay (base64)
- Confidence scores
- Alert history (derived from detections)

---

## Backend Components

```
backend/
├── main.py              # FastAPI app, routes, startup
├── inference.py         # Mock inference (swap for real model later)
├── agent.py             # CatchLogAgent: classify, decide, alert
├── database.py          # SQLite setup + CRUD operations
├── models.py            # Pydantic schemas
├── regulations.json     # Species regulatory data
└── audio/
    ├── alert_info.mp3
    ├── alert_warning.mp3
    └── alert_critical.mp3
```

### Component Responsibilities

| Component | Does | Doesn't |
|-----------|------|---------|
| `main.py` | Routes, CORS, serves audio files, startup | Business logic |
| `inference.py` | Image → species + bbox + confidence | Know about regulations |
| `agent.py` | Check regulations, decide alert level, log to DB | Handle HTTP, inference |
| `database.py` | SQLite CRUD, detection history queries | Business decisions |
| `models.py` | Pydantic models for validation/serialization | Logic |

### Mock Inference Behavior

Until real model is integrated:
- Randomly picks from species list
- Weighted distribution: ~70% legal, ~20% bycatch, ~10% protected
- Random bbox within image bounds
- Confidence range: 0.75-0.98

---

## Frontend Components

```
frontend/
├── app/
│   ├── page.tsx              # Main dashboard layout
│   ├── layout.tsx            # Root layout
│   └── globals.css           # Tailwind base
├── components/
│   ├── ImageUpload.tsx       # Drag-drop or click to upload
│   ├── VideoFeed.tsx         # Shows last frame with bbox
│   ├── CatchCounter.tsx      # Species count table
│   ├── AlertFeed.tsx         # Scrolling alert log
│   ├── ComplianceSummary.tsx # Trip stats + status badge
│   └── ReleaseButton.tsx     # Mark as released action
├── lib/
│   └── api.ts                # Fetch helpers
└── package.json
```

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  CATCHLOG                                        [Upload Image] │
├───────────────────────────────────┬─────────────────────────────┤
│                                   │   CATCH COUNTER             │
│   VIDEO FEED                      │   ─────────────────────     │
│   ┌───────────────────────────┐   │   Albacore Tuna    12      │
│   │                           │   │   Bigeye Tuna       8      │
│   │   [Image + bbox overlay]  │   │   Blue Shark        1 ⚠️   │
│   │                           │   ├─────────────────────────────┤
│   └───────────────────────────┘   │   COMPLIANCE                │
│                                   │   Total: 21 | Legal: 20    │
│   [Release Button] (if needed)    │   Status: ✓ COMPLIANT      │
├───────────────────────────────────┴─────────────────────────────┤
│   ALERT FEED                                                    │
│   14:23:05  ● Bigeye Tuna detected (Legal)                     │
│   14:23:12  ⚠️ BYCATCH: Blue Shark — Release required          │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. User clicks "Upload Image" or drags file
2. `POST /api/upload` sends image to backend
3. Backend runs inference, logs to DB, returns detection
4. Frontend updates VideoFeed, plays audio if alert
5. Frontend polls `GET /api/state` every 2s for counts/compliance
6. If bycatch/protected shown, Release button appears
7. User clicks Release → `POST /api/release` → compliance updates

---

## Scope Boundaries

### In Scope (POC)
- Single image upload → detect → display
- Mock inference (swappable for real model)
- SQLite audit log
- Voice alerts via frontend audio playback
- Mock release feature
- Compliance summary

### Out of Scope
- Multi-trip / multi-vessel / multi-org
- Video streaming / batch upload
- Real-time camera feed
- User authentication
- PDF report export
- Mobile responsive

### Optional (if time permits)
- Batch image upload (simulate video)
- Live camera feed

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Mock inference | Teammate handles model; keeps backend testable independently |
| Single `/api/state` endpoint | Simple polling, fewer failure modes |
| SQLite over in-memory | Audit trail required for compliance story |
| Lean schema (18 bytes/detection) | On-device storage optimization |
| Frontend plays audio | Portable, no system dependencies |
| No trip modeling | Single demo session, YAGNI |

---

## Next Steps

1. Set up backend project with uv
2. Implement database.py + models.py
3. Implement mock inference.py
4. Implement agent.py
5. Implement main.py (FastAPI routes)
6. Set up frontend project with bun
7. Build components in order: Upload → VideoFeed → Counter → Alerts → Compliance → Release
8. Integration testing
9. Swap mock inference for real model when ready
