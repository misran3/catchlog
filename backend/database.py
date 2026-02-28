"""SQLite database operations for catch logging."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "catch_log.db"

# Species seed data: (id, name, status)
# Status: 0=legal, 1=bycatch, 2=protected, 3=unknown
SPECIES_DATA = [
    (1, "Albacore Tuna", 0),      # legal
    (2, "Bigeye Tuna", 0),        # legal
    (3, "Mahi-Mahi", 0),          # legal
    (4, "Yellowfin Tuna", 0),     # legal (new)
    (5, "Shark", 1),              # bycatch (was Blue Shark)
    (6, "Opah", 1),               # bycatch (new)
    (7, "Pelagic Stingray", 2),   # protected (was Sea Turtle)
    (8, "Unknown", 3),            # unknown
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
