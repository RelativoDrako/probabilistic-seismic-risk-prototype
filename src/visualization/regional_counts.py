from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


def export_regional_event_counts(region_counts: dict[str, int], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    regions = list(region_counts.keys())
    counts = [region_counts[r] for r in regions]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(regions, counts)
    ax.set_title("Accepted curated events by region")
    ax.set_xlabel("Region")
    ax.set_ylabel("Event count")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path
