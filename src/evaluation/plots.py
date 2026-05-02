from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def save_roc_curve(path: str | Path, fpr: list[float], tpr: list[float]) -> None:
    target = Path(path)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(fpr, tpr, label="ROC")
    ax.plot([0, 1], [0, 1], linestyle="--", color="grey")
    ax.set_title("ROC Curve")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.legend()
    fig.tight_layout()
    fig.savefig(target)
    plt.close(fig)


def save_pr_curve(path: str | Path, recall: list[float], precision: list[float]) -> None:
    target = Path(path)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(recall, precision, label="PR")
    ax.set_title("Precision-Recall Curve")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.legend()
    fig.tight_layout()
    fig.savefig(target)
    plt.close(fig)


def save_probability_histogram(path: str | Path, probabilities: list[float]) -> None:
    target = Path(path)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(probabilities, bins=10, range=(0.0, 1.0))
    ax.set_title("Predicted Probability Histogram")
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(target)
    plt.close(fig)
