# backend/models.py
"""Pydantic models for API request/response validation."""

from enum import IntEnum
from pydantic import BaseModel


class SpeciesStatus(IntEnum):
    """Species regulatory status."""
    LEGAL = 0
    BYCATCH = 1
    PROTECTED = 2
    UNKNOWN = 3


class AlertLevel(str):
    """Alert severity levels."""
    NONE = "none"
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Detection(BaseModel):
    """Single detection result from inference."""
    detection_id: int
    timestamp: str
    species: str
    status: str  # legal | bycatch | protected | unknown
    confidence: float
    bbox: list[int]  # [x1, y1, x2, y2]
    alert_level: str
    audio_url: str | None = None


class Alert(BaseModel):
    """Alert entry for the feed."""
    timestamp: str
    message: str
    level: str


class Compliance(BaseModel):
    """Compliance summary statistics."""
    total: int
    legal: int
    bycatch: int
    protected: int
    released: int
    status: str  # COMPLIANT | ACTION_REQUIRED


class AppState(BaseModel):
    """Full application state for dashboard."""
    last_detection: Detection | None = None
    frame_base64: str | None = None
    counts: dict[str, int]
    alerts: list[Alert]
    compliance: Compliance


class ReleaseResponse(BaseModel):
    """Response from release endpoint."""
    released_id: int
    species: str
    compliance_status: str
