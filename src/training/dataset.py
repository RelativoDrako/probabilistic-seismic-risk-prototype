from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass


FEATURE_COLUMNS = [
    "event_count",
    "max_magnitude",
    "mean_magnitude",
    "mean_depth_km",
    "recent_rate_7d",
    "recent_rate_30d",
    "rolling_delta_rate",
    "days_since_last_event",
]


@dataclass(frozen=True)
class TrainingRow:
    feature_row_id: str
    generation_id: str
    region_code: str
    region_name: str
    window_end_utc: str
    features: list[float]
    target_label: float

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["feature_names"] = FEATURE_COLUMNS
        return payload


def _as_float(value: object | None, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def load_training_rows(connection: sqlite3.Connection, feature_generation_id: str) -> list[TrainingRow]:
    rows = connection.execute(
        """
        SELECT feature_row_id,
               generation_id,
               COALESCE(region_code, region_name) AS region_code,
               region_name,
               window_end_utc,
               event_count,
               max_magnitude,
               mean_magnitude,
               mean_depth_km,
               recent_rate_7d,
               recent_rate_30d,
               rolling_delta_rate,
               COALESCE(days_since_last_event, 9999.0) AS days_since_last_event,
               COALESCE(target_label, target_risk_label) AS target_label
        FROM region_features
        WHERE generation_id = ?
        ORDER BY window_end_utc ASC, region_name ASC
        """,
        (feature_generation_id,),
    ).fetchall()
    training_rows: list[TrainingRow] = []
    for row in rows:
        if row["target_label"] is None:
            continue
        training_rows.append(
            TrainingRow(
                feature_row_id=row["feature_row_id"],
                generation_id=row["generation_id"],
                region_code=row["region_code"],
                region_name=row["region_name"],
                window_end_utc=row["window_end_utc"],
                features=[
                    _as_float(row["event_count"]),
                    _as_float(row["max_magnitude"]),
                    _as_float(row["mean_magnitude"]),
                    _as_float(row["mean_depth_km"]),
                    _as_float(row["recent_rate_7d"]),
                    _as_float(row["recent_rate_30d"]),
                    _as_float(row["rolling_delta_rate"]),
                    _as_float(row["days_since_last_event"], default=9999.0),
                ],
                target_label=float(row["target_label"]),
            )
        )
    return training_rows
