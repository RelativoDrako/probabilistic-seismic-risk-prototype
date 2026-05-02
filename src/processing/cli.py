from __future__ import annotations

import argparse
import sys

from src.common.settings import load_settings
from src.common.sqlite import connect_sqlite
from src.processing.curation_service import curate_ingest_batch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Curate one ingest batch into curated_events.")
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--ingest-batch-id", required=True)
    parser.add_argument("--curation-version", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings()
    with connect_sqlite(settings.sqlite_path) as conn:
        summary = curate_ingest_batch(
            conn=conn,
            source_id=args.source_id,
            ingest_batch_id=args.ingest_batch_id,
            curation_version=args.curation_version,
        )
    for key, value in summary.items():
        print(f"[ok] {key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
