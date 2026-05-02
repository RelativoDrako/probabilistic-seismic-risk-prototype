from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def export_risk_heatmap(feature_rows: list[dict], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not feature_rows:
        data = pd.DataFrame([[0.0]], index=["NO_DATA"], columns=["risk_score"])
    else:
        rows = []
        for row in feature_rows:
            score = float(row.get("event_count") or 0) + float(row.get("mean_magnitude") or 0)
            rows.append({"region_code": row["region_code"], "risk_score": score})
        data = pd.DataFrame(rows).set_index("region_code")

    fig, ax = plt.subplots(figsize=(8, 4))
    im = ax.imshow(data.values.reshape(-1, 1), aspect="auto")
    ax.set_title("Prototype relative regional risk heatmap")
    ax.set_yticks(range(len(data.index)))
    ax.set_yticklabels(list(data.index))
    ax.set_xticks([0])
    ax.set_xticklabels(["risk_score"])
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path
