from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import joblib
from sklearn.model_selection import train_test_split

from src.common.settings import load_settings
from src.common.sqlite import connect_sqlite
from src.common.target_contract import TARGET_DEFINITION
from src.evaluation.metrics import compute_classification_metrics
from src.training.dataset_builder import build_training_dataset


def _always_negative(size: int) -> list[int]:
    return [0] * size


def _build_xy(dataset: list[dict]) -> tuple[list[list[float]], list[int]]:
    X = [
        [
            row["event_count"],
            row["max_magnitude"],
            row["mean_magnitude"],
            row["mean_depth_km"],
            row["days_since_last_event"],
        ]
        for row in dataset
    ]
    y = [row["target_label"] for row in dataset]
    return X, y


def _eval_model(model, X_test, y_test) -> tuple[dict, list[float] | None]:
    y_pred = model.predict(X_test)
    y_prob = None
    if hasattr(model, "predict_proba"):
        try:
            y_prob = model.predict_proba(X_test)[:, 1].tolist()
        except Exception:
            y_prob = None
    payload = compute_classification_metrics(y_test, y_pred, y_prob)
    return payload | {"threshold": 0.5}, y_prob


def _threshold_sweep(y_true, y_prob: list[float]) -> list[dict]:
    out = []
    for i in range(10, 91, 5):
        threshold = i / 100.0
        y_pred = [1 if p >= threshold else 0 for p in y_prob]
        metrics = compute_classification_metrics(y_true, y_pred, y_prob)
        out.append({
            "threshold": threshold,
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1": metrics["f1"],
            "balanced_accuracy": metrics["balanced_accuracy"],
            "pr_auc": metrics["pr_auc"],
            "positive_prediction_rate": metrics["positive_prediction_rate"],
        })
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate current baseline, balanced baseline, and threshold sweep.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--ingest-batch-id", required=True)
    parser.add_argument("--feature-set-version", required=True)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    settings = load_settings()
    reports_dir = repo_root / "artifacts" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    current_model_path = repo_root / "artifacts" / "models" / "baseline_model.joblib"
    balanced_model_path = repo_root / "artifacts" / "models" / "balanced_baseline_model.joblib"

    with connect_sqlite(settings.sqlite_path) as conn:
        dataset = build_training_dataset(conn, args.ingest_batch_id, args.feature_set_version)

    if len(dataset) < 2:
        raise ValueError("Not enough rows to evaluate variants.")

    X, y = _build_xy(dataset)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.4, random_state=42, stratify=y if len(set(y)) > 1 else None
    )

    current_model = joblib.load(current_model_path)
    current_metrics, _ = _eval_model(current_model, X_test, y_test)

    balanced_model = joblib.load(balanced_model_path)
    balanced_metrics, y_prob_balanced = _eval_model(balanced_model, X_test, y_test)

    always_negative_metrics = compute_classification_metrics(y_test, _always_negative(len(y_test)), None)

    comparison = {
        "target_definition": TARGET_DEFINITION,
        "ingest_batch_id": args.ingest_batch_id,
        "feature_set_version": args.feature_set_version,
        "dataset_rows": len(dataset),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "variants": {
            "current_baseline": current_metrics,
            "balanced_baseline": balanced_metrics,
            "always_negative": always_negative_metrics,
        },
    }

    comparison_path = reports_dir / "baseline_variants_comparison.json"
    comparison_path.write_text(json.dumps(comparison, indent=2), encoding="utf-8")

    if y_prob_balanced is not None:
        threshold_sweep = _threshold_sweep(y_test, y_prob_balanced)
        best_by_f1 = max(threshold_sweep, key=lambda x: x["f1"]) if threshold_sweep else None
        best_by_bal_acc = max(threshold_sweep, key=lambda x: x["balanced_accuracy"]) if threshold_sweep else None
        threshold_payload = {
            "target_definition": TARGET_DEFINITION,
            "ingest_batch_id": args.ingest_batch_id,
            "feature_set_version": args.feature_set_version,
            "best_by_f1": best_by_f1,
            "best_by_balanced_accuracy": best_by_bal_acc,
            "thresholds": threshold_sweep,
        }
        sweep_path = reports_dir / "threshold_sweep.json"
        sweep_path.write_text(json.dumps(threshold_payload, indent=2), encoding="utf-8")
        print(f"[ok] threshold_sweep_path={sweep_path.as_posix()}")
        if best_by_f1:
            print(f"[ok] best_threshold_by_f1={best_by_f1['threshold']}")
            print(f"[ok] best_f1={best_by_f1['f1']:.6f}")
        if best_by_bal_acc:
            print(f"[ok] best_threshold_by_balanced_accuracy={best_by_bal_acc['threshold']}")
            print(f"[ok] best_balanced_accuracy={best_by_bal_acc['balanced_accuracy']:.6f}")
    else:
        print("[warn] balanced_baseline has no usable predict_proba; threshold sweep skipped")

    print(f"[ok] baseline_variants_comparison_path={comparison_path.as_posix()}")
    print(f"[ok] current_baseline_balanced_accuracy={current_metrics['balanced_accuracy']:.6f}")
    print(f"[ok] balanced_baseline_balanced_accuracy={balanced_metrics['balanced_accuracy']:.6f}")
    print(f"[ok] always_negative_balanced_accuracy={always_negative_metrics['balanced_accuracy']:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
