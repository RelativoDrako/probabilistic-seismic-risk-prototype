from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib.pyplot as plt


def export_metrics_panel(metrics_payload: dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"Model: {metrics_payload.get('model', 'n/a')}",
        f"Accuracy: {metrics_payload.get('accuracy', 0):.4f}",
        f"Precision: {metrics_payload.get('precision', 0):.4f}",
        f"Recall: {metrics_payload.get('recall', 0):.4f}",
        f"F1: {metrics_payload.get('f1', 0):.4f}",
    ]

    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.axis("off")
    ax.set_title("Metrics panel", fontsize=14)
    ax.text(0.02, 0.9, "\n".join(lines), va="top", fontsize=11)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        try:
            fig.tight_layout()
        except Exception:
            pass

    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def export_model_summary_panel(summary_payload: dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"Ingest batch: {summary_payload.get('ingest_batch_id', 'n/a')}",
        f"Feature set: {summary_payload.get('feature_set_version', 'n/a')}",
        f"Dataset rows: {summary_payload.get('dataset_rows', 'n/a')}",
        f"Train rows: {summary_payload.get('train_rows', 'n/a')}",
        f"Test rows: {summary_payload.get('test_rows', 'n/a')}",
        f"Split: {summary_payload.get('split_rule', 'n/a')}",
        "Target:",
        str(summary_payload.get("target_definition", "n/a")),
    ]

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.axis("off")
    ax.set_title("Model summary panel", fontsize=14)
    ax.text(0.02, 0.95, "\n".join(lines), va="top", fontsize=10)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        try:
            fig.tight_layout()
        except Exception:
            pass

    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path
