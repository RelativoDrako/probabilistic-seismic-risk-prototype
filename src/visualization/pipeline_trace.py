from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib.pyplot as plt


def export_pipeline_trace(
    *,
    raw_assets_count: int,
    curated_events_count: int,
    feature_rows_count: int,
    has_model_artifact: bool,
    has_metrics_report: bool,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    labels = [
        f"Raw assets\n{raw_assets_count}",
        f"Curated events\n{curated_events_count}",
        f"Region features\n{feature_rows_count}",
        f"Model artifact\n{'yes' if has_model_artifact else 'no'}",
        f"Metrics report\n{'yes' if has_metrics_report else 'no'}",
    ]
    x = [0, 1, 2, 3, 4]
    y = [1, 1, 1, 1, 1]

    fig, ax = plt.subplots(figsize=(12, 2.8))
    ax.axis("off")

    for i, label in enumerate(labels):
        ax.text(
            x[i], y[i], label,
            ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.5", linewidth=1.2)
        )
        if i < len(labels) - 1:
            ax.annotate(
                "",
                xy=(x[i + 1] - 0.25, y[i]),
                xytext=(x[i] + 0.25, y[i]),
                arrowprops=dict(arrowstyle="->", lw=1.4),
            )

    ax.set_title("Prototype pipeline trace", fontsize=14)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        try:
            fig.tight_layout()
        except Exception:
            pass

    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path
