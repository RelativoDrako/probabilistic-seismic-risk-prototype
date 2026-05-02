from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


def export_magnitude_distribution(magnitudes: list[float], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    if magnitudes:
        ax.hist(magnitudes, bins=min(12, max(5, len(magnitudes))), edgecolor="black")
    ax.set_title("Magnitude distribution (accepted curated events)")
    ax.set_xlabel("Magnitude")
    ax.set_ylabel("Frequency")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path
