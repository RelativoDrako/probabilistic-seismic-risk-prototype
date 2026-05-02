from __future__ import annotations

import sqlite3

from src.common.clock import utc_now_iso
from src.common.ids import build_feature_generation_id
from src.features.models import RegionFeatureRow


def start_feature_generation(conn: sqlite3.Connection, ingest_batch_id: str, feature_set_version: str, window_spec: str) -> str:
    feature_generation_id = build_feature_generation_id(
        feature_set_version=feature_set_version,
        window_spec=window_spec,
        source_batch_scope=ingest_batch_id,
    )
    conn.execute(
        """
        INSERT INTO feature_generations (
            feature_generation_id,
            feature_set_version,
            window_spec,
            grain,
            source_batch_scope,
            started_at_utc,
            completed_at_utc,
            status,
            row_count
        )
        VALUES (?, ?, ?, 'region', ?, ?, NULL, 'started', 0)
        ON CONFLICT(feature_generation_id) DO UPDATE SET
            status='started',
            completed_at_utc=NULL
        """,
        (feature_generation_id, feature_set_version, window_spec, ingest_batch_id, utc_now_iso()),
    )
    conn.commit()
    return feature_generation_id


def complete_feature_generation(conn: sqlite3.Connection, feature_generation_id: str, row_count: int) -> None:
    conn.execute(
        """
        UPDATE feature_generations
        SET status='completed', completed_at_utc=?, row_count=?
        WHERE feature_generation_id = ?
        """,
        (utc_now_iso(), row_count, feature_generation_id),
    )
    conn.commit()


def fail_feature_generation(conn: sqlite3.Connection, feature_generation_id: str) -> None:
    conn.execute(
        """
        UPDATE feature_generations
        SET status='failed', completed_at_utc=?
        WHERE feature_generation_id = ?
        """,
        (utc_now_iso(), feature_generation_id),
    )
    conn.commit()


def insert_region_features(conn, rows):
    for row in rows:
        conn.execute(
            """
            INSERT INTO region_features (
                feature_row_id,
                feature_generation_id,
                feature_set_version,
                region_code,
                window_start_utc,
                window_end_utc,
                event_count,
                max_magnitude,
                mean_magnitude,
                mean_depth_km,
                days_since_last_event,
                target_label,
                created_at_utc
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(feature_generation_id, region_code, window_start_utc, window_end_utc) DO UPDATE SET
                feature_set_version=excluded.feature_set_version,
                event_count=excluded.event_count,
                max_magnitude=excluded.max_magnitude,
                mean_magnitude=excluded.mean_magnitude,
                mean_depth_km=excluded.mean_depth_km,
                days_since_last_event=excluded.days_since_last_event,
                target_label=excluded.target_label,
                created_at_utc=excluded.created_at_utc
            """,
            (
                row.feature_row_id,
                row.feature_generation_id,
                row.feature_set_version,
                row.region_code,
                row.window_start_utc,
                row.window_end_utc,
                row.event_count,
                row.max_magnitude,
                row.mean_magnitude,
                row.mean_depth_km,
                row.days_since_last_event,
                row.target_label,
                row.created_at_utc,
            ),
        )
    conn.commit()
    return len(rows)



def list_region_features_by_generation(conn: sqlite3.Connection, feature_generation_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM region_features WHERE feature_generation_id = ? ORDER BY region_code",
        (feature_generation_id,),
    ).fetchall()
    return [dict(r) for r in rows]
