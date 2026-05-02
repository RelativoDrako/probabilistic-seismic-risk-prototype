from __future__ import annotations

import sqlite3

from src.common.ids import build_event_id
from src.processing.models import CandidateEvent


def build_event_identity_key(candidate: CandidateEvent) -> str:
    if candidate.occurred_at_utc is None or candidate.latitude is None or candidate.longitude is None:
        raise ValueError("Candidate event lacks minimum identity fields.")
    return build_event_id(
        source_id=candidate.source_id,
        source_event_key=candidate.source_event_key,
        occurred_at_utc=candidate.occurred_at_utc,
        latitude=candidate.latitude,
        longitude=candidate.longitude,
    )


def detect_duplicate(conn: sqlite3.Connection, candidate: CandidateEvent, curation_version: str) -> str | None:
    event_id = build_event_identity_key(candidate)
    row = conn.execute(
        """
        SELECT event_id
        FROM curated_events
        WHERE event_id = ? AND curation_version = ?
        """,
        (event_id, curation_version),
    ).fetchone()
    return None if row is None else row["event_id"]
