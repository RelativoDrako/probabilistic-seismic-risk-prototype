from __future__ import annotations

import sqlite3

from src.common.clock import utc_now_iso
from src.common.contracts import TABLE_INGEST_BATCHES
from src.common.ids import build_ingest_batch_id


def start_ingest_batch(
    conn: sqlite3.Connection,
    source_id: str,
    batch_label: str,
    ingest_mode: str,
    source_snapshot_ref: str | None,
) -> str:
    ingest_batch_id = build_ingest_batch_id(source_id=source_id, batch_label=batch_label)

    existing = conn.execute(
        f"""
        SELECT ingest_batch_id, source_id, batch_label, source_snapshot_ref,
               ingest_mode, status
        FROM {TABLE_INGEST_BATCHES}
        WHERE ingest_batch_id = ?
        """,
        (ingest_batch_id,),
    ).fetchone()

    if existing is None:
        conn.execute(
            f"""
            INSERT INTO {TABLE_INGEST_BATCHES} (
                ingest_batch_id,
                source_id,
                batch_label,
                source_snapshot_ref,
                ingest_mode,
                started_at_utc,
                completed_at_utc,
                status,
                raw_file_count,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, NULL, 'started', 0, NULL)
            """,
            (
                ingest_batch_id,
                source_id,
                batch_label,
                source_snapshot_ref,
                ingest_mode,
                utc_now_iso(),
            ),
        )
        conn.commit()
        return ingest_batch_id

    conflict_fields: dict[str, tuple[object, object]] = {}
    expected = {
        "source_id": source_id,
        "batch_label": batch_label,
        "source_snapshot_ref": source_snapshot_ref,
        "ingest_mode": ingest_mode,
    }

    for field_name, expected_value in expected.items():
        existing_value = existing[field_name]
        if existing_value != expected_value:
            conflict_fields[field_name] = (existing_value, expected_value)

    if conflict_fields:
        raise ValueError(
            f"Batch conflict for ingest_batch_id={ingest_batch_id!r}. "
            f"Existing batch has different semantic scope: {conflict_fields}"
        )

    return ingest_batch_id


def complete_ingest_batch(conn: sqlite3.Connection, ingest_batch_id: str, raw_file_count: int) -> None:
    row = conn.execute(
        f"""
        SELECT raw_file_count, status
        FROM {TABLE_INGEST_BATCHES}
        WHERE ingest_batch_id = ?
        """,
        (ingest_batch_id,),
    ).fetchone()

    if row is None:
        raise ValueError(f"Cannot complete missing ingest batch: {ingest_batch_id}")

    existing_count = int(row["raw_file_count"])
    if existing_count not in (0, raw_file_count):
        raise ValueError(
            f"Ingest batch {ingest_batch_id!r} already has raw_file_count={existing_count}, "
            f"which conflicts with new count={raw_file_count}."
        )

    conn.execute(
        f"""
        UPDATE {TABLE_INGEST_BATCHES}
        SET status = 'completed',
            raw_file_count = ?,
            completed_at_utc = ?
        WHERE ingest_batch_id = ?
        """,
        (raw_file_count, utc_now_iso(), ingest_batch_id),
    )
    conn.commit()


def fail_ingest_batch(conn: sqlite3.Connection, ingest_batch_id: str, message: str) -> None:
    conn.execute(
        f"""
        UPDATE {TABLE_INGEST_BATCHES}
        SET status = 'failed',
            completed_at_utc = ?,
            notes = ?
        WHERE ingest_batch_id = ?
        """,
        (utc_now_iso(), message, ingest_batch_id),
    )
    conn.commit()
