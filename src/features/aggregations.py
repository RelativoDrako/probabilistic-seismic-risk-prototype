from __future__ import annotations

import math
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from src.common.clock import utc_now_iso
from src.common.contracts import FEATURE_SET_VERSION_V1
from src.common.ids import make_feature_row_id

from .labels import compute_target_label
from .models import AcceptedCuratedEvent, RegionFeatureRecord
from .windowing import build_window_days, parse_utc_timestamp, window_bounds


UTC = timezone.utc


def normalize_region_code(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return "_".join(part for part in normalized.upper().replace("-", " ").split() if part)


def _safe_mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_feature_rows(
    generation_id: str,
    accepted_events: list[AcceptedCuratedEvent],
    feature_set_version: str = FEATURE_SET_VERSION_V1,
) -> list[RegionFeatureRecord]:
    events_by_region: dict[str, list[AcceptedCuratedEvent]] = defaultdict(list)
    for event in accepted_events:
        events_by_region[event.region_code].append(event)

    rows: list[RegionFeatureRecord] = []
    for region_code, region_events in events_by_region.items():
        ordered_region_events = sorted(region_events, key=lambda item: item.event_time_utc)
        min_day = parse_utc_timestamp(ordered_region_events[0].event_time_utc).date()
        max_day = parse_utc_timestamp(ordered_region_events[-1].event_time_utc).date()
        for window_end_day in build_window_days(min_day, max_day, target_horizon_days=7):
            window_start_utc, window_end_utc = window_bounds(window_end_day, lookback_days=30)
            window_start = parse_utc_timestamp(window_start_utc)
            window_end = parse_utc_timestamp(window_end_utc)
            history_events = [
                event
                for event in ordered_region_events
                if window_start <= parse_utc_timestamp(event.event_time_utc) <= window_end
            ]
            magnitudes = [event.magnitude for event in history_events if event.magnitude is not None]
            depths = [event.depth_km for event in history_events if event.depth_km is not None]
            recent_7d_threshold = window_end - timedelta(days=6)
            recent_7d_count = sum(
                1
                for event in history_events
                if parse_utc_timestamp(event.event_time_utc) >= recent_7d_threshold
            )
            latest_event_time = max((parse_utc_timestamp(event.event_time_utc) for event in history_events), default=None)
            days_since_last_event = (
                float((window_end - latest_event_time).days)
                if latest_event_time is not None
                else 9999.0
            )
            target_label = compute_target_label(window_end_utc, ordered_region_events)
            row = RegionFeatureRecord(
                feature_row_id=make_feature_row_id(region_code, window_start_utc, window_end_utc, feature_set_version),
                generation_id=generation_id,
                region_code=region_code,
                region_name=ordered_region_events[0].state_name,
                window_start_utc=window_start_utc,
                window_end_utc=window_end_utc,
                event_count=len(history_events),
                mean_magnitude=round(_safe_mean(magnitudes), 6),
                max_magnitude=max(magnitudes) if magnitudes else 0.0,
                mean_depth_km=round(_safe_mean(depths), 6),
                recent_rate_7d=round(recent_7d_count / 7.0, 6),
                recent_rate_30d=round(len(history_events) / 30.0, 6),
                rolling_delta_rate=round((recent_7d_count / 7.0) - (len(history_events) / 30.0), 6),
                days_since_last_event=days_since_last_event,
                target_label=target_label,
                target_risk_label=int(target_label),
                target_risk_score=round(max(recent_7d_count / 7.0, 0.0), 6),
                feature_set_version=feature_set_version,
                created_at_utc=utc_now_iso(),
            )
            rows.append(row)
    return sorted(rows, key=lambda item: (item.window_end_utc, item.region_code))
