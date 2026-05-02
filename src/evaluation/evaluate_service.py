from __future__ import annotations

import json
from pathlib import Path

import joblib
from sklearn.model_selection import train_test_split

from src.common.target_contract import TARGET_DEFINITION
from src.evaluation.metrics import compute_classification_metrics
from src.evaluation.report_builder import write_evaluation_summary, write_metrics_json
from src.training.dataset_builder import build_training_dataset


def _always_negative_predictions(size: int) -> list[int]:
    return [0] * size


def evaluate_baseline(conn, ingest_batch_id: str, feature_set_version: str, model_path: Path, reports_dir: Path) -> dict:
    dataset = build_training_dataset(conn, ingest_batch_id, feature_set_version)
    if len(dataset) < 2:
        raise ValueError("Not enough rows to evaluate baseline model.")

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

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.4, random_state=42, stratify=y if len(set(y)) > 1 else None
    )

    model = joblib.load(model_path)
    y_pred = model.predict(X_test)

    y_prob = None
    if hasattr(model, "predict_proba"):
        try:
            y_prob = model.predict_proba(X_test)[:, 1]
        except Exception:
            y_prob = None

    metrics = compute_classification_metrics(y_test, y_pred, y_prob)

    baseline_pred = _always_negative_predictions(len(y_test))
    baseline_metrics = compute_classification_metrics(y_test, baseline_pred, None)

    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "baseline_comparison.json").write_text(
        json.dumps(
            {
                "target_definition": TARGET_DEFINITION,
                "current_model": {
                    "model": "baseline_random_forest",
                    **metrics,
                },
                "always_negative": baseline_metrics,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (reports_dir / "confusion_matrix.json").write_text(
        json.dumps(
            {
                "model": "baseline_random_forest",
                "target_definition": TARGET_DEFINITION,
                "confusion_matrix": metrics["confusion_matrix"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = {
        "model": "baseline_random_forest",
        "ingest_batch_id": ingest_batch_id,
        "feature_set_version": feature_set_version,
        "dataset_rows": len(dataset),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "split_rule": "random_holdout_test_size_0.4_stratified_if_possible",
        "target_definition": TARGET_DEFINITION,
        **metrics,
    }

    write_metrics_json(reports_dir / "metrics.json", payload)
    write_evaluation_summary(reports_dir / "evaluation_summary.md", payload)
    return payload
