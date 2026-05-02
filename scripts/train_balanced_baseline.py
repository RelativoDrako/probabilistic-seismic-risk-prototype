from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from src.common.settings import load_settings
from src.common.sqlite import connect_sqlite
from src.common.target_contract import TARGET_DEFINITION
from src.training.dataset_builder import build_training_dataset


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Train class_weight=balanced baseline.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--ingest-batch-id", required=True)
    parser.add_argument("--feature-set-version", required=True)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    settings = load_settings()
    model_path = repo_root / "artifacts" / "models" / "balanced_baseline_model.joblib"
    model_path.parent.mkdir(parents=True, exist_ok=True)

    with connect_sqlite(settings.sqlite_path) as conn:
        dataset = build_training_dataset(conn, args.ingest_batch_id, args.feature_set_version)

    if len(dataset) < 2:
        raise ValueError("Not enough rows to train balanced baseline.")

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

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced",
        min_samples_leaf=1,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    joblib.dump(model, model_path)

    positive_ratio = sum(y) / len(y) if y else 0.0
    negative_ratio = 1.0 - positive_ratio if y else 0.0

    meta = {
        "model_name": "balanced_random_forest",
        "model_path": str(model_path),
        "random_state": 42,
        "class_weight": "balanced",
        "dataset_rows": len(dataset),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "split_rule": "random_holdout_test_size_0.4_stratified_if_possible",
        "target_definition": TARGET_DEFINITION,
        "positive_ratio": positive_ratio,
        "negative_ratio": negative_ratio,
        "feature_columns": [
            "event_count",
            "max_magnitude",
            "mean_magnitude",
            "mean_depth_km",
            "days_since_last_event",
        ],
    }
    meta_path = model_path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"[ok] model_path={model_path.as_posix()}")
    print(f"[ok] model_meta_path={meta_path.as_posix()}")
    print(f"[ok] dataset_rows={len(dataset)}")
    print(f"[ok] train_rows={len(X_train)}")
    print(f"[ok] test_rows={len(X_test)}")
    print(f"[ok] positive_ratio={positive_ratio:.6f}")
    print(f"[ok] negative_ratio={negative_ratio:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
