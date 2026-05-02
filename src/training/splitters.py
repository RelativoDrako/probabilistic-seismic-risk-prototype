from __future__ import annotations

from collections import defaultdict

from .dataset import TrainingRow


def temporal_split(rows: list[TrainingRow], train_fraction: float = 0.8) -> tuple[list[TrainingRow], list[TrainingRow]]:
    if len(rows) < 4:
        raise ValueError("At least 4 feature rows are required for temporal training/evaluation split")
    by_window: dict[str, list[TrainingRow]] = defaultdict(list)
    for row in rows:
        by_window[row.window_end_utc].append(row)
    ordered_windows = sorted(by_window)
    if len(ordered_windows) < 2:
        raise ValueError("At least two distinct temporal windows are required for split")
    split_index = int(len(ordered_windows) * train_fraction)
    split_index = max(1, min(len(ordered_windows) - 1, split_index))
    train_windows = set(ordered_windows[:split_index])
    test_windows = set(ordered_windows[split_index:])
    train_rows = [row for row in rows if row.window_end_utc in train_windows]
    test_rows = [row for row in rows if row.window_end_utc in test_windows]
    if not train_rows or not test_rows:
        raise ValueError("Temporal split produced an empty train or test slice")
    return train_rows, test_rows
