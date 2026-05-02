from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


_REGION_COORDS = {
    "MX_NORTH": (-102.0, 26.0),
    "MX_CENTRAL": (-99.0, 20.0),
    "MX_SOUTH": (-96.5, 16.5),
}


def export_probabilistic_risk_map(region_scores: dict[str, float], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_title("Prototype probabilistic regional risk surface")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_xlim(-118, -86)
    ax.set_ylim(14, 33)
    ax.grid(alpha=0.25)

    xs, ys, sizes = [], [], []
    labels = []
    for region_code, (lon, lat) in _REGION_COORDS.items():
        xs.append(lon)
        ys.append(lat)
        score = float(region_scores.get(region_code, 0.0))
        sizes.append(300 + score * 150)
        labels.append(f"{region_code}\nscore={score:.2f}")

    scatter = ax.scatter(xs, ys, s=sizes, alpha=0.7)
    for x, y, label in zip(xs, ys, labels):
        ax.text(x, y, label, ha="center", va="center", fontsize=9)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path
