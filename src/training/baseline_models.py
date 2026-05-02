from __future__ import annotations

from sklearn.ensemble import RandomForestClassifier


def build_baseline_model() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=50,
        random_state=42,
        max_depth=4,
    )
