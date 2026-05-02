from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureGenerationRecord:
    feature_generation_id: str
    feature_set_version: str
    window_spec: str
    grain: str
    source_batch_scope: str
    started_at_utc: str
    completed_at_utc: str | None
    status: str
    row_count: int


@dataclass(frozen=True)
class RegionFeatureRow:
    feature_row_id: str
    feature_generation_id: str
    feature_set_version: str
    region_code: str
    window_start_utc: str
    window_end_utc: str
    event_count: int
    max_magnitude: float | None
    mean_magnitude: float | None
    mean_depth_km: float | None
    days_since_last_event: float | None
    target_label: float | None
    created_at_utc: str
