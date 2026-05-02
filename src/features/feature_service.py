from __future__ import annotations

import sqlite3

from src.common.ids import build_pipeline_run_id
from src.common.clock import utc_now_iso
from src.features.builders import build_region_feature_rows
from src.features.repository import (
    complete_feature_generation,
    fail_feature_generation,
    insert_region_features,
    start_feature_generation,
)


def _journal(conn: sqlite3.Connection, stage_name: str, stage_run_key: str, related_entity_id: str | None, status: str, message: str, completed: bool) -> None:
    pipeline_run_id = build_pipeline_run_id(stage_name, stage_run_key)
    started_at = utc_now_iso()
    completed_at = utc_now_iso() if completed else None
    conn.execute(
        """
        INSERT INTO pipeline_run_journal (
            pipeline_run_id, stage_name, stage_run_key, related_entity_id,
            status, started_at_utc, completed_at_utc, message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(stage_name, stage_run_key) DO UPDATE SET
            related_entity_id=excluded.related_entity_id,
            status=excluded.status,
            completed_at_utc=excluded.completed_at_utc,
            message=excluded.message
        """,
        (pipeline_run_id, stage_name, stage_run_key, related_entity_id, status, started_at, completed_at, message),
    )
    conn.commit()


def build_region_features(conn: sqlite3.Connection, ingest_batch_id: str, feature_set_version: str, window_spec: str) -> str:
    stage_name = "feature_build"
    stage_run_key = f"{ingest_batch_id}:{feature_set_version}:{window_spec}"
    _journal(conn, stage_name, stage_run_key, ingest_batch_id, "started", "feature generation started", False)

    feature_generation_id = start_feature_generation(
        conn=conn,
        ingest_batch_id=ingest_batch_id,
        feature_set_version=feature_set_version,
        window_spec=window_spec,
    )

    try:
        rows = conn.execute(
            """
            SELECT *
            FROM curated_events
            WHERE ingest_batch_id = ? AND record_status = 'accepted'
            ORDER BY occurred_at_utc
            """,
            (ingest_batch_id,),
        ).fetchall()
        events = [dict(r) for r in rows]
        feature_rows = build_region_feature_rows(
            events=events,
            window_spec=window_spec,
            feature_set_version=feature_set_version,
            feature_generation_id=feature_generation_id,
        )
        total_rows = insert_region_features(conn, feature_rows)
        complete_feature_generation(conn, feature_generation_id, total_rows)
        _journal(conn, stage_name, stage_run_key, feature_generation_id, "completed", f"feature rows={total_rows}", True)
        return feature_generation_id
    except Exception:
        fail_feature_generation(conn, feature_generation_id)
        _journal(conn, stage_name, stage_run_key, feature_generation_id, "failed", "feature generation failed", True)
        raise
