from __future__ import annotations

import sqlite3
from typing import Any

from src.common.target_contract import TARGET_DEFINITION


def build_training_dataset(conn: sqlite3.Connection, ingest_batch_id: str, feature_set_version: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT rf.*
        FROM region_features rf
        JOIN feature_generations fg
          ON fg.feature_generation_id = rf.feature_generation_id
        WHERE fg.source_batch_scope = ? AND rf.feature_set_version = ?
        ORDER BY rf.region_code, rf.window_start_utc
        """,
        (ingest_batch_id, feature_set_version),
    ).fetchall()

    dataset: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        dataset.append(
            {
                "region_code": item["region_code"],
                "event_count": float(item["event_count"] or 0),
                "max_magnitude": float(item["max_magnitude"] or 0.0),
                "mean_magnitude": float(item["mean_magnitude"] or 0.0),
                "mean_depth_km": float(item["mean_depth_km"] or 0.0),
                "days_since_last_event": float(item["days_since_last_event"] or 0.0),
                "target_label": int(item["target_label"] or 0),
                "target_definition": TARGET_DEFINITION,
            }
        )
    return dataset
