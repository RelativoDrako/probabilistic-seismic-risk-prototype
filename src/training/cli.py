from __future__ import annotations

import argparse
import sys

from src.common.settings import load_settings
from src.common.sqlite import connect_sqlite
from src.training.train_service import train_baseline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train baseline model from region features.")
    parser.add_argument("--ingest-batch-id", required=True)
    parser.add_argument("--feature-set-version", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings()
    model_output_path = settings.artifacts_dir / "models" / "baseline_model.joblib"

    with connect_sqlite(settings.sqlite_path) as conn:
        summary = train_baseline(
            conn=conn,
            ingest_batch_id=args.ingest_batch_id,
            feature_set_version=args.feature_set_version,
            model_output_path=model_output_path,
        )

    print(f"[ok] model_path={summary['model_path']}")
    print(f"[ok] model_meta_path={summary['model_meta_path']}")
    print(f"[ok] dataset_rows={summary['dataset_rows']}")
    print(f"[ok] train_rows={summary['train_rows']}")
    print(f"[ok] test_rows={summary['test_rows']}")
    print(f"[ok] positive_ratio={summary['positive_ratio']:.6f}")
    print(f"[ok] negative_ratio={summary['negative_ratio']:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
