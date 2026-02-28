# backend/agent.py
"""CatchLog Agent - decision engine for detection processing."""

import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from PIL import Image
import io
import base64

from models import Detection, Alert, Compliance, AppState, AlertLevel
from database import (
    get_species_by_name,
    log_detection,
    get_detection_counts,
    get_compliance_stats,
    mark_released,
    get_last_unreleased_alert,
)
from inference import run_inference, InferenceResult


# Alert level mapping by species status
STATUS_TO_ALERT = {
    0: AlertLevel.NONE,      # Legal
    1: AlertLevel.WARNING,   # Bycatch
    2: AlertLevel.CRITICAL,  # Protected
    3: AlertLevel.INFO,      # Unknown
}

STATUS_NAMES = {
    0: "legal",
    1: "bycatch",
    2: "protected",
    3: "unknown",
}

AUDIO_URLS = {
    AlertLevel.WARNING: "/audio/alert_warning.mp3",
    AlertLevel.CRITICAL: "/audio/alert_critical.mp3",
    AlertLevel.INFO: "/audio/alert_info.mp3",
}


@dataclass
class AgentState:
    """In-memory state for the agent."""
    last_detection: Detection | None = None
    frame_base64: str | None = None
    alerts: list[Alert] = field(default_factory=list)


# Global agent state
_state = AgentState()


def process_image(image: Image.Image) -> Detection:
    """
    Process an uploaded image through the full pipeline.

    1. Run inference
    2. Look up species regulation
    3. Log to database
    4. Generate alert if needed
    5. Update in-memory state
    """
    # Run inference
    result: InferenceResult = run_inference(image)

    # Get species info from DB
    species_info = get_species_by_name(result.species)
    if not species_info:
        # Fallback to Unknown
        species_info = get_species_by_name("Unknown")

    # Log to database
    ts = int(time.time())
    detection_id = log_detection(ts, species_info["id"])

    # Determine alert level
    status_code = species_info["status"]
    alert_level = STATUS_TO_ALERT.get(status_code, AlertLevel.INFO)
    status_name = STATUS_NAMES.get(status_code, "unknown")

    # Get audio URL if alert needed
    audio_url = AUDIO_URLS.get(alert_level) if alert_level != AlertLevel.NONE else None

    # Create detection object
    timestamp = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    detection = Detection(
        detection_id=detection_id,
        timestamp=timestamp,
        species=result.species,
        status=status_name,
        confidence=result.confidence,
        bbox=result.bbox,
        alert_level=alert_level,
        audio_url=audio_url,
    )

    # Draw bbox on image and encode
    frame_with_bbox = _draw_bbox(image.copy(), result.bbox, status_code)
    _state.frame_base64 = _image_to_base64(frame_with_bbox)

    # Update state
    _state.last_detection = detection

    # Add to alerts if not legal
    if alert_level != AlertLevel.NONE:
        alert_msg = _format_alert_message(result.species, status_name)
        _state.alerts.append(Alert(
            timestamp=timestamp,
            message=alert_msg,
            level=alert_level,
        ))
        # Keep last 50 alerts
        _state.alerts = _state.alerts[-50:]

    return detection


def _draw_bbox(image: Image.Image, bbox: list[int], status: int) -> Image.Image:
    """Draw bounding box on image with color based on status."""
    from PIL import ImageDraw

    colors = {
        0: "#22c55e",  # Green - legal
        1: "#eab308",  # Yellow - bycatch
        2: "#ef4444",  # Red - protected
        3: "#6b7280",  # Gray - unknown
    }
    color = colors.get(status, "#6b7280")

    draw = ImageDraw.Draw(image)
    x1, y1, x2, y2 = bbox
    draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

    return image


def _image_to_base64(image: Image.Image) -> str:
    """Convert PIL Image to base64 data URL."""
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}"


def _format_alert_message(species: str, status: str) -> str:
    """Format alert message based on status."""
    if status == "bycatch":
        return f"BYCATCH: {species} — Release required"
    elif status == "protected":
        return f"PROTECTED: {species} — Immediate release required"
    elif status == "unknown":
        return f"UNKNOWN: {species} — Flagged for review"
    return f"{species} detected"


def get_state() -> AppState:
    """Get current application state for dashboard."""
    counts = get_detection_counts()
    stats = get_compliance_stats()

    compliance = Compliance(
        total=stats["total"],
        legal=stats["legal"],
        bycatch=stats["bycatch"],
        protected=stats["protected"],
        released=stats["released"],
        status=stats["status"],
    )

    return AppState(
        last_detection=_state.last_detection,
        frame_base64=_state.frame_base64,
        counts=counts,
        alerts=_state.alerts,
        compliance=compliance,
    )


def release_last() -> dict | None:
    """
    Mark the last unreleased bycatch/protected as released.

    Returns release info or None if nothing to release.
    """
    unreleased = get_last_unreleased_alert()
    if not unreleased:
        return None

    mark_released(unreleased["id"])
    stats = get_compliance_stats()

    return {
        "released_id": unreleased["id"],
        "species": unreleased["name"],
        "compliance_status": stats["status"],
    }


def reset_state() -> None:
    """Reset agent state (for testing)."""
    global _state
    _state = AgentState()
