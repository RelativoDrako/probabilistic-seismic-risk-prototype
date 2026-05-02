from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.common.contracts import TARGET_HORIZON_DAYS, TARGET_MAGNITUDE_THRESHOLD

from .models import AcceptedCuratedEvent
from .windowing import parse_utc_timestamp


UTC = timezone.utc


def compute_target_label(window_end_utc: str, region_events: list[AcceptedCuratedEvent]) -> float:
    window_end = parse_utc_timestamp(window_end_utc)
    horizon_end = window_end + timedelta(days=TARGET_HORIZON_DAYS)
    for event in region_events:
        event_time = parse_utc_timestamp(event.event_time_utc)
        if window_end < event_time <= horizon_end and (event.magnitude or 0.0) >= TARGET_MAGNITUDE_THRESHOLD:
            return 1.0
    return 0.0
