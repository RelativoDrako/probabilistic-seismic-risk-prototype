from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from src.common.paths import get_sqlite_path


def _ensure_columns(conn: sqlite3.Connection, table_name: str, required: dict[str, str]) -> None:
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
    for name, coltype in required.items():
        if name not in existing:
            if "PRIMARY KEY" in coltype:
                continue
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {name} {coltype}")


def _ensure_sources_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sources (
            source_id TEXT PRIMARY KEY,
            source_name TEXT,
            source_kind TEXT,
            provider TEXT
        )
        """
    )
    _ensure_columns(
        conn,
        "sources",
        {
            "source_id": "TEXT PRIMARY KEY",
            "source_name": "TEXT",
            "source_kind": "TEXT",
            "provider": "TEXT",
            "country_scope": "TEXT",
            "source_url": "TEXT",
            "license_note": "TEXT",
            "license_url": "TEXT",
            "source_description": "TEXT",
            "source_citation": "TEXT",
            "is_active": "INTEGER DEFAULT 1",
            "created_at_utc": "TEXT",
            "updated_at_utc": "TEXT",
        },
    )


def _ensure_ingest_batches_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ingest_batches (
            ingest_batch_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            batch_label TEXT,
            ingest_mode TEXT
        )
        """
    )
    _ensure_columns(
        conn,
        "ingest_batches",
        {
            "ingest_batch_id": "TEXT PRIMARY KEY",
            "source_id": "TEXT NOT NULL",
            "batch_label": "TEXT",
            "source_snapshot_ref": "TEXT",
            "ingest_mode": "TEXT",
            "started_at_utc": "TEXT",
            "completed_at_utc": "TEXT",
            "status": "TEXT",
            "raw_file_count": "INTEGER DEFAULT 0",
            "notes": "TEXT",
        },
    )


def _ensure_raw_asset_manifest_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_asset_manifest (
            raw_asset_id TEXT PRIMARY KEY,
            ingest_batch_id TEXT NOT NULL,
            relative_path TEXT NOT NULL
        )
        """
    )
    _ensure_columns(
        conn,
        "raw_asset_manifest",
        {
            "raw_asset_id": "TEXT PRIMARY KEY",
            "ingest_batch_id": "TEXT NOT NULL",
            "source_id": "TEXT",
            "relative_path": "TEXT NOT NULL",
            "file_name": "TEXT",
            "content_sha256": "TEXT",
            "file_size_bytes": "INTEGER",
            "content_type": "TEXT",
            "source_published_at_utc": "TEXT",
            "downloaded_at_utc": "TEXT",
            "manifest_version": "TEXT",
            "is_active": "INTEGER DEFAULT 1",
            "sha256": "TEXT",
            "row_count": "INTEGER DEFAULT 0",
            "created_at_utc": "TEXT",
        },
    )


def _ensure_curated_events_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS curated_events (
            event_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            ingest_batch_id TEXT NOT NULL,
            source_event_key TEXT,
            occurred_at_utc TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            depth_km REAL,
            magnitude_value REAL,
            magnitude_type TEXT,
            region_code TEXT,
            municipality_code TEXT,
            curation_version TEXT,
            record_status TEXT,
            raw_asset_id TEXT,
            inserted_at_utc TEXT,
            updated_at_utc TEXT
        )
        """
    )


def _ensure_feature_generations_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS feature_generations (
            feature_generation_id TEXT PRIMARY KEY,
            feature_set_version TEXT NOT NULL,
            window_spec TEXT NOT NULL,
            grain TEXT NOT NULL,
            source_batch_scope TEXT NOT NULL,
            started_at_utc TEXT,
            completed_at_utc TEXT,
            status TEXT,
            row_count INTEGER DEFAULT 0
        )
        """
    )


def _ensure_region_features_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS region_features (
            feature_row_id TEXT PRIMARY KEY,
            feature_generation_id TEXT NOT NULL,
            feature_set_version TEXT NOT NULL,
            region_code TEXT NOT NULL,
            window_start_utc TEXT NOT NULL,
            window_end_utc TEXT NOT NULL,
            event_count INTEGER,
            max_magnitude REAL,
            mean_magnitude REAL,
            mean_depth_km REAL,
            days_since_last_event REAL,
            target_label REAL,
            created_at_utc TEXT
        )
        """
    )


def _ensure_pipeline_run_journal_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_run_journal (
            pipeline_run_id TEXT PRIMARY KEY,
            stage_name TEXT NOT NULL,
            stage_run_key TEXT NOT NULL,
            related_entity_id TEXT,
            status TEXT,
            started_at_utc TEXT,
            completed_at_utc TEXT,
            message TEXT,
            UNIQUE(stage_name, stage_run_key)
        )
        """
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap SQLite schema for the seismic prototype.")
    parser.add_argument("--sqlite-path", default=None)
    args = parser.parse_args(argv)

    sqlite_path = Path(args.sqlite_path).resolve() if args.sqlite_path else get_sqlite_path()
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(sqlite_path))
    try:
        _ensure_sources_schema(conn)
        _ensure_ingest_batches_schema(conn)
        _ensure_raw_asset_manifest_schema(conn)
        _ensure_curated_events_schema(conn)
        _ensure_feature_generations_schema(conn)
        _ensure_region_features_schema(conn)
        _ensure_pipeline_run_journal_schema(conn)
        conn.commit()
    finally:
        conn.close()

    print(f"[ok] sqlite_bootstrap={sqlite_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())