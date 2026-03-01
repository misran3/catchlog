# Cloud Compliance Agent Design

## Overview

Add agentic cloud compliance review that triggers when vessel returns to connectivity. An LLM agent reviews the audit log against regional regulations, generates a compliance report, and autonomously sends email alerts for unresolved violations.

## Goals

1. **Agentic Behavior**: LLM autonomously decides what info to fetch and whether to send alerts
2. **Compliance Report**: Structured analysis of trip catches with violation details
3. **Automated Action**: Email notification when violations require attention

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│  [Sync to Cloud] button → POST /api/sync                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│  1. Load audit log from SQLite                                  │
│  2. Call cloud compliance agent                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COMPLIANCE AGENT                              │
│  Pydantic AI + Bedrock (Claude)                                 │
│                                                                  │
│  Tools:                                                         │
│  • get_species_regulation(species) → regulation info            │
│  • send_alert_email(to, subject, body) → sends via SES          │
│                                                                  │
│  Output: ComplianceReport (structured)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AWS SES                                     │
│  (Only if violations detected - agent decides)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Models

```python
class TripSummary(BaseModel):
    total_catches: int
    legal: int
    bycatch: int
    protected: int
    released: int
    unreleased_violations: int

class Violation(BaseModel):
    species: str
    status: str  # "bycatch" or "protected"
    count: int
    fine_per_incident: int
    total_fine: int
    explanation: str  # Why this is a violation

class ComplianceReport(BaseModel):
    trip_summary: TripSummary
    violations: list[Violation]
    regional_context: str        # Brief context about this region's rules
    potential_penalties: str     # Total fines, consequences
    recommendation: str          # What they should do
    severity: Literal["compliant", "minor", "major", "critical"]
    email_sent: bool             # Whether alert was triggered
```

---

## Regulations Map

```python
# In-memory regulations for Pacific Region
PACIFIC_REGULATIONS = {
    "Albacore Tuna": {
        "status": "legal",
        "fine": 0,
        "summary": "Target species for commercial longline fishing. No catch limits in international waters."
    },
    "Bigeye Tuna": {
        "status": "legal",
        "fine": 0,
        "summary": "High-value target species. Quota managed by WCPFC."
    },
    "Mahi-Mahi": {
        "status": "legal",
        "fine": 0,
        "summary": "Legal target species. No restrictions."
    },
    "Yellowfin Tuna": {
        "status": "legal",
        "fine": 0,
        "summary": "Target species. Subject to annual quotas."
    },
    "Shark": {
        "status": "bycatch",
        "fine": 500,
        "summary": "Bycatch species. Must release alive when possible. Finning prohibited. $500 fine per unreleased shark."
    },
    "Opah": {
        "status": "bycatch",
        "fine": 250,
        "summary": "Non-target species. Should release to minimize ecosystem impact. $250 fine if retained."
    },
    "Pelagic Stingray": {
        "status": "protected",
        "fine": 5000,
        "summary": "Protected under Pacific Marine Conservation Act. Immediate release required. $5,000 fine per incident. Three violations triggers license suspension."
    },
    "Unknown": {
        "status": "unknown",
        "fine": 100,
        "summary": "Unidentified species must be logged and reported. $100 administrative fee if not properly documented."
    },
}
```

---

## Agent Tools

```python
@agent.tool
def get_species_regulation(species: str) -> dict:
    """Look up fishing regulations for a species in the Pacific region."""
    return PACIFIC_REGULATIONS.get(species, {
        "status": "unknown",
        "fine": 0,
        "summary": "No regulatory data available for this species."
    })

@agent.tool
def send_alert_email(to: str, subject: str, body: str) -> bool:
    """Send compliance alert email via AWS SES.
    Use when violations require immediate notification to compliance officers."""
    # AWS SES send logic
    return True
```

---

## Agent System Prompt

```
You are a fishing compliance officer reviewing audit logs from commercial vessels.

Your job:
1. Review the audit log provided
2. Look up regulations for each species using get_species_regulation tool
3. Identify any violations (unreleased bycatch or protected species)
4. Generate a compliance report
5. If there are unreleased violations, send an alert email using send_alert_email tool

Be thorough. For each species in the log, check its regulation status.
Calculate total fines based on violation counts and fine amounts.

Severity levels:
- compliant: No violations
- minor: Only unreleased bycatch, small fines (<$1000)
- major: Multiple bycatch or any protected species
- critical: Unreleased protected species
```

---

## API

**Endpoint:** `POST /api/sync`

**Response:** `ComplianceReport`

---

## Agent Flow

1. User clicks "Sync to Cloud" button
2. Backend fetches audit log from SQLite (all detections with species, status, released flag)
3. Agent receives: system prompt + formatted audit log as user message
4. Agent calls `get_species_regulation()` for each unique species (tool use)
5. Agent reasons about violations (unreleased bycatch/protected)
6. Agent generates structured `ComplianceReport`
7. If `severity != "compliant"` → Agent calls `send_alert_email()`
8. Return report to frontend for display

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Claude via AWS Bedrock |
| Agent Framework | Pydantic AI (Bedrock provider) |
| Email | AWS SES |
| Structured Output | Pydantic models |

---

## Files to Create/Modify

| File | Purpose |
|------|---------|
| `backend/compliance_agent.py` | Agent definition, tools, regulations map |
| `backend/email_service.py` | AWS SES integration |
| `backend/main.py` | Add `/api/sync` endpoint |
| `backend/models.py` | Add ComplianceReport models |
| `frontend/components/SyncButton.tsx` | Sync to Cloud button |
| `frontend/components/ComplianceReport.tsx` | Display report |

---

## Environment Variables

```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
SES_FROM_EMAIL=compliance@example.com
SES_TO_EMAIL=officer@example.com
```
