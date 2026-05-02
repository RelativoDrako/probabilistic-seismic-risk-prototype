from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.common.settings import load_settings
from src.common.sqlite import connect_sqlite, ensure_sqlite_parent_dir
from src.ingestion.ingest_service import run_ingest_with_summary
from src.ingestion.models import SourceDefinition


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Register a source, manifest raw files, and count readable records."
    )
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--source-kind", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--raw-input-dir", required=True)
    parser.add_argument("--batch-label", required=True)
    parser.add_argument("--ingest-mode", required=True)
    parser.add_argument("--source-url", default=None)
    parser.add_argument("--license-note", default=None)
    parser.add_argument("--source-snapshot-ref", default=None)
    parser.add_argument("--country-scope", default="MX")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = load_settings()
    db_path = settings.sqlite_path
    ensure_sqlite_parent_dir(db_path)

    raw_input_dir = Path(args.raw_input_dir).resolve()
    if not raw_input_dir.exists():
        parser.error(f"--raw-input-dir does not exist: {raw_input_dir}")
    if not raw_input_dir.is_dir():
        parser.error(f"--raw-input-dir is not a directory: {raw_input_dir}")

    source_definition = SourceDefinition(
        source_id=args.source_id,
        source_name=args.source_name,
        source_kind=args.source_kind,
        provider=args.provider,
        source_url=args.source_url,
        license_note=args.license_note,
        country_scope=args.country_scope,
        is_active=1,
    )

    with connect_sqlite(db_path) as conn:
        summary = run_ingest_with_summary(
            conn=conn,
            source_definition=source_definition,
            batch_label=args.batch_label,
            raw_input_dir=raw_input_dir,
            ingest_mode=args.ingest_mode,
            source_snapshot_ref=args.source_snapshot_ref,
        )

    print(f"[ok] ingest_batch_id={summary.ingest_batch_id}")
    print(f"[ok] files_registered={summary.file_count}")
    print(f"[ok] records_read={summary.record_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
