from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

DB_REL = Path("artifacts/sqlite/seismic_prototype.db")


def ensure_columns(conn: sqlite3.Connection, table_name: str, required: dict[str, str]) -> None:
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
    for name, coltype in required.items():
        if name not in existing:
            if "PRIMARY KEY" in coltype:
                continue
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {name} {coltype}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Idempotent runtime schema migration.")
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    db_path = repo_root / DB_REL
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
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
        ensure_columns(conn, "sources", {
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
        })

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
        ensure_columns(conn, "ingest_batches", {
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
        })

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS raw_asset_manifest (
                raw_asset_id TEXT PRIMARY KEY,
                ingest_batch_id TEXT NOT NULL,
                relative_path TEXT NOT NULL
            )
            """
        )
        ensure_columns(conn, "raw_asset_manifest", {
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
        })

        conn.commit()
    finally:
        conn.close()

    print(f"[ok] migrated_runtime_schema={db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())