from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

DB_REL = Path("artifacts/sqlite/seismic_prototype.db")

REQUIRED_COLUMNS = {
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
}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Idempotent migration for sources schema.")
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

        existing = {
            row[1]: row[2]
            for row in conn.execute("PRAGMA table_info(sources)").fetchall()
        }

        for name, coltype in REQUIRED_COLUMNS.items():
            if name not in existing:
                if "PRIMARY KEY" in coltype:
                    continue
                conn.execute(f"ALTER TABLE sources ADD COLUMN {name} {coltype}")

        conn.commit()

    finally:
        conn.close()

    print(f"[ok] migrated_sources_schema={db_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
