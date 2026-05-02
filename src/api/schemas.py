from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class SummaryResponse(BaseModel):
    latest_feature_generation: dict[str, Any] | None
    latest_model_run: dict[str, Any] | None
    latest_evaluation: dict[str, Any] | None


class RegionLatestResponse(BaseModel):
    region_code: str
    region_name: str
    window_start_utc: str
    window_end_utc: str
    event_count: int
    mean_magnitude: float
    max_magnitude: float
    mean_depth_km: float
    recent_rate_7d: float
    recent_rate_30d: float
    rolling_delta_rate: float
    days_since_last_event: float
    target_label: float
    target_risk_score: float


class EvaluationLatestResponse(BaseModel):
    evaluation_report_id: str | None
    model_run_id: str | None
    metrics: dict[str, float] | None
    report_json_path: str | None
    report_md_path: str | None
    roc_plot_path: str | None
    pr_plot_path: str | None
    prob_hist_path: str | None
