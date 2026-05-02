from __future__ import annotations

from pathlib import Path
import json


def write_metrics_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_evaluation_summary(path: Path, payload: dict) -> None:
    text = f"""# Evaluation Summary

- model: {payload['model']}
- ingest_batch_id: {payload['ingest_batch_id']}
- feature_set_version: {payload['feature_set_version']}
- dataset_rows: {payload['dataset_rows']}
- train_rows: {payload['train_rows']}
- test_rows: {payload['test_rows']}
- split_rule: {payload['split_rule']}
- target_definition: {payload['target_definition']}

## Metrics
- accuracy: {payload['accuracy']:.4f}
- precision: {payload['precision']:.4f}
- recall: {payload['recall']:.4f}
- f1: {payload['f1']:.4f}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
