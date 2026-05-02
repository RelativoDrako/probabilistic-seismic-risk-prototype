from __future__ import annotations

import argparse
import sys

from src.common.settings import load_settings
from src.common.sqlite import connect_sqlite
from src.features.feature_service import build_region_features
from src.features.repository import list_region_features_by_generation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build region features from curated events.")
    parser.add_argument("--ingest-batch-id", required=True)
    parser.add_argument("--feature-set-version", required=True)
    parser.add_argument("--window-spec", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings()
    with connect_sqlite(settings.sqlite_path) as conn:
        feature_generation_id = build_region_features(
            conn=conn,
            ingest_batch_id=args.ingest_batch_id,
            feature_set_version=args.feature_set_version,
            window_spec=args.window_spec,
        )
        rows = list_region_features_by_generation(conn, feature_generation_id)
    print(f"[ok] feature_generation_id={feature_generation_id}")
    print(f"[ok] rows_generated={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
