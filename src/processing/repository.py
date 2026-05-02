from __future__ import annotations

import sqlite3

from src.processing.models import CuratedEventRecord


def upsert_curated_events(conn: sqlite3.Connection, rows: list[CuratedEventRecord]) -> int:
    total = 0
    for row in rows:
        conn.execute(
            """
            INSERT INTO curated_events (
                event_id,
                source_id,
                ingest_batch_id,
                source_event_key,
                occurred_at_utc,
                latitude,
                longitude,
                depth_km,
                magnitude_value,
                magnitude_type,
                region_code,
                municipality_code,
                curation_version,
                record_status,
                raw_asset_id,
                inserted_at_utc,
                updated_at_utc
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO UPDATE SET
                updated_at_utc = excluded.updated_at_utc,
                record_status = excluded.record_status,
                magnitude_value = excluded.magnitude_value,
                magnitude_type = excluded.magnitude_type,
                depth_km = excluded.depth_km,
                region_code = excluded.region_code,
                municipality_code = excluded.municipality_code
            """,
            (
                row.event_id,
                row.source_id,
                row.ingest_batch_id,
                row.source_event_key,
                row.occurred_at_utc,
                row.latitude,
                row.longitude,
                row.depth_km,
                row.magnitude_value,
                row.magnitude_type,
                row.region_code,
                row.municipality_code,
                row.curation_version,
                row.record_status,
                row.raw_asset_id,
                row.inserted_at_utc,
                row.updated_at_utc,
            ),
        )
        total += 1
    conn.commit()
    return total


def find_existing_event(conn: sqlite3.Connection, event_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM curated_events WHERE event_id = ?",
        (event_id,),
    ).fetchone()
    return None if row is None else dict(row)


def list_curated_events_by_batch(conn: sqlite3.Connection, ingest_batch_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM curated_events WHERE ingest_batch_id = ? ORDER BY occurred_at_utc",
        (ingest_batch_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def count_curated_statuses_by_batch(conn: sqlite3.Connection, ingest_batch_id: str) -> dict:
    rows = conn.execute(
        """
        SELECT record_status, COUNT(*) AS total
        FROM curated_events
        WHERE ingest_batch_id = ?
        GROUP BY record_status
        """,
        (ingest_batch_id,),
    ).fetchall()
    return {row["record_status"]: int(row["total"]) for row in rows}
