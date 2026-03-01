"""SQLite database operations for catch logging."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "catch_log.db"

# Species seed data: (id, name, status)
# Status: 0=legal, 1=bycatch, 2=protected, 3=unknown
# Matches train_full.py TARGET_SPECIES exactly
SPECIES_DATA = [
    # Legal (status=0)
    (1, "Albacore Tuna", 0),
    (2, "Yellowfin Tuna", 0),
    (3, "Bigeye Tuna", 0),
    (4, "Skipjack Tuna", 0),
    (5, "Mahi-Mahi", 0),
    (6, "Swordfish", 0),
    (7, "Wahoo", 0),
    (8, "Shortbill Spearfish", 0),
    (9, "Long Snouted Lancetfish", 0),
    (10, "Great Barracuda", 0),
    (11, "Sickle Pomfret", 0),
    (12, "Pomfret", 0),
    (13, "Rainbow Runner", 0),
    (14, "Snake Mackerel", 0),
    (15, "Roudie Scolar", 0),
    # Bycatch (status=1)
    (16, "Shark", 1),
    (17, "Thresher Shark", 1),
    (18, "Opah", 1),
    (19, "Oilfish", 1),
    (20, "Mola Mola", 1),
    # Protected (status=2)
    (21, "Pelagic Stingray", 2),
    (22, "Striped Marlin", 2),
    (23, "Blue Marlin", 2),
    (24, "Black Marlin", 2),
    (25, "Indo Pacific Sailfish", 2),
    # Unknown (status=3)
    (26, "Unknown", 3),
]


def init_db() -> None:
    """Initialize database schema and seed data."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS species (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                status INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL,
                species_id INTEGER NOT NULL,
                released INTEGER DEFAULT 0,
                FOREIGN KEY (species_id) REFERENCES species(id)
            );
        """)

        # Seed species if empty
        cursor = conn.execute("SELECT COUNT(*) FROM species")
        if cursor.fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO species (id, name, status) VALUES (?, ?, ?)",
                SPECIES_DATA
            )
        conn.commit()


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_species_by_id(species_id: int) -> dict | None:
    """Get species info by ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, name, status FROM species WHERE id = ?",
            (species_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_species_by_name(name: str) -> dict | None:
    """Get species info by name."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, name, status FROM species WHERE name = ?",
            (name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_species() -> list[dict]:
    """Get all species."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT id, name, status FROM species")
        return [dict(row) for row in cursor.fetchall()]


def log_detection(ts: int, species_id: int) -> int:
    """Log a detection, return the new detection ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO detections (ts, species_id) VALUES (?, ?)",
            (ts, species_id)
        )
        conn.commit()
        return cursor.lastrowid


def mark_released(detection_id: int) -> bool:
    """Mark a detection as released. Returns True if updated."""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE detections SET released = 1 WHERE id = ? AND released = 0",
            (detection_id,)
        )
        conn.commit()
        return cursor.rowcount > 0


def get_last_unreleased_alert() -> dict | None:
    """Get the most recent unreleased bycatch/protected detection."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT d.id, d.ts, s.name, s.status
            FROM detections d
            JOIN species s ON d.species_id = s.id
            WHERE d.released = 0 AND s.status IN (1, 2)
            ORDER BY d.id DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        return dict(row) if row else None


def get_detection_counts() -> dict[str, int]:
    """Get count of detections per species."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT s.name, COUNT(*) as count
            FROM detections d
            JOIN species s ON d.species_id = s.id
            GROUP BY s.name
        """)
        return {row["name"]: row["count"] for row in cursor.fetchall()}


def get_compliance_stats() -> dict:
    """Get compliance statistics."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total,
                COALESCE(SUM(CASE WHEN s.status = 0 THEN 1 ELSE 0 END), 0) as legal,
                COALESCE(SUM(CASE WHEN s.status = 1 THEN 1 ELSE 0 END), 0) as bycatch,
                COALESCE(SUM(CASE WHEN s.status = 2 THEN 1 ELSE 0 END), 0) as protected,
                COALESCE(SUM(CASE WHEN d.released = 1 THEN 1 ELSE 0 END), 0) as released
            FROM detections d
            JOIN species s ON d.species_id = s.id
        """)
        row = cursor.fetchone()
        stats = dict(row)

        # Determine compliance status
        unreleased_issues = (stats["bycatch"] + stats["protected"]) - stats["released"]
        stats["status"] = "COMPLIANT" if unreleased_issues <= 0 else "ACTION_REQUIRED"

        return stats


def reset_db() -> None:
    """Reset database (for testing)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM detections")
        conn.commit()


def get_audit_log() -> list[dict]:
    """Get all detections as audit log for compliance review."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT
                d.id,
                d.ts,
                s.name as species,
                s.status,
                d.released
            FROM detections d
            JOIN species s ON d.species_id = s.id
            ORDER BY d.ts ASC
        """)

        rows = cursor.fetchall()
        return [
            {
                "id": row["id"],
                "timestamp": row["ts"],
                "species": row["species"],
                "status": ["legal", "bycatch", "protected", "unknown"][row["status"]],
                "released": bool(row["released"]),
            }
            for row in rows
        ]


def format_audit_log_for_agent(detections: list[dict]) -> str:
    """Format audit log as a string for the compliance agent."""
    if not detections:
        return "No catches recorded."

    lines = ["CATCH LOG:", "=" * 40]

    for d in detections:
        released_str = " (RELEASED)" if d["released"] else ""
        lines.append(
            f"- {d['species']} | Status: {d['status']} | ID: {d['id']}{released_str}"
        )

    # Add summary
    total = len(detections)
    by_status = {}
    released = sum(1 for d in detections if d["released"])

    for d in detections:
        by_status[d["status"]] = by_status.get(d["status"], 0) + 1

    lines.append("=" * 40)
    lines.append(f"TOTAL: {total} catches")
    lines.append(f"  Legal: {by_status.get('legal', 0)}")
    lines.append(f"  Bycatch: {by_status.get('bycatch', 0)}")
    lines.append(f"  Protected: {by_status.get('protected', 0)}")
    lines.append(f"  Unknown: {by_status.get('unknown', 0)}")
    lines.append(f"  Released: {released}")

    return "\n".join(lines)
