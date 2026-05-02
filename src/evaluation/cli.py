from __future__ import annotations

import argparse
import sys

from src.common.settings import load_settings
from src.common.sqlite import connect_sqlite
from src.evaluation.evaluate_service import evaluate_baseline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate baseline model and export reports.")
    parser.add_argument("--ingest-batch-id", required=True)
    parser.add_argument("--feature-set-version", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings()
    model_path = settings.artifacts_dir / "models" / "baseline_model.joblib"
    reports_dir = settings.artifacts_dir / "reports"

    with connect_sqlite(settings.sqlite_path) as conn:
        payload = evaluate_baseline(
            conn=conn,
            ingest_batch_id=args.ingest_batch_id,
            feature_set_version=args.feature_set_version,
            model_path=model_path,
            reports_dir=reports_dir,
        )

    print(f"[ok] metrics_path={(reports_dir / 'metrics.json').as_posix()}")
    print(f"[ok] evaluation_summary_path={(reports_dir / 'evaluation_summary.md').as_posix()}")
    print(f"[ok] baseline_comparison_path={(reports_dir / 'baseline_comparison.json').as_posix()}")
    print(f"[ok] confusion_matrix_path={(reports_dir / 'confusion_matrix.json').as_posix()}")
    print(f"[ok] accuracy={payload['accuracy']:.4f}")
    print(f"[ok] balanced_accuracy={payload['balanced_accuracy']:.4f}")
    print(f"[ok] pr_auc={payload['pr_auc'] if payload['pr_auc'] is not None else 'n/a'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
