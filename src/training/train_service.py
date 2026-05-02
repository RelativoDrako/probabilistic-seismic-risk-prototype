from __future__ import annotations

import json
from pathlib import Path

import joblib
from sklearn.model_selection import train_test_split

from src.training.baseline_models import build_baseline_model
from src.training.dataset_builder import build_training_dataset
from src.common.target_contract import TARGET_DEFINITION


def train_baseline(conn, ingest_batch_id: str, feature_set_version: str, model_output_path: Path) -> dict:
    dataset = build_training_dataset(conn, ingest_batch_id, feature_set_version)
    if len(dataset) < 2:
        raise ValueError("Not enough feature rows to train baseline model.")

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

    positive_ratio = sum(y) / len(y) if y else 0.0
    negative_ratio = 1.0 - positive_ratio if y else 0.0

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.4, random_state=42, stratify=y if len(set(y)) > 1 else None
    )

    model = build_baseline_model()
    model.fit(X_train, y_train)

    model_output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_output_path)

    meta_payload = {
        "model_name": "baseline_random_forest",
        "random_state": 42,
        "model_path": str(model_output_path),
        "dataset_rows": len(dataset),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "split_rule": "random_holdout_test_size_0.4_stratified_if_possible",
        "target_definition": TARGET_DEFINITION,
        "feature_columns": [
            "event_count",
            "max_magnitude",
            "mean_magnitude",
            "mean_depth_km",
            "days_since_last_event",
        ],
        "positive_ratio": positive_ratio,
        "negative_ratio": negative_ratio,
    }
    meta_path = model_output_path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")

    return {
        "model_name": "baseline_random_forest",
        "model_path": str(model_output_path),
        "model_meta_path": str(meta_path),
        "dataset_rows": len(dataset),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "split_rule": "random_holdout_test_size_0.4_stratified_if_possible",
        "target_definition": TARGET_DEFINITION,
        "positive_ratio": positive_ratio,
        "negative_ratio": negative_ratio,
    }
