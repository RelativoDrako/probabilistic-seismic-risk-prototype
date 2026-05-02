from __future__ import annotations

from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def compute_classification_metrics(y_true, y_pred, y_prob=None) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    payload = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
        "positive_prediction_rate": float(sum(y_pred) / len(y_pred)) if y_pred is not None and len(y_pred) else 0.0,
        "prevalence": float(sum(y_true) / len(y_true)) if y_true is not None and len(y_true) else 0.0,
    }
    if y_prob is not None:
        try:
            payload["pr_auc"] = float(average_precision_score(y_true, y_prob))
        except Exception:
            payload["pr_auc"] = None
    else:
        payload["pr_auc"] = None
    return payload
