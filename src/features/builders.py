from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from statistics import mean

from src.common.clock import utc_now_iso
from src.common.ids import build_feature_row_id
from src.features.models import RegionFeatureRow
from src.features.windowing import generate_sliding_windows

# Fase 1.2:
# - priorizar spatial bins reproducibles para elevar diversidad espacial
# - endurecer la definición de label para mitigar el desbalance extremo
SPATIAL_BIN_DEGREES = 0.5
FUTURE_EVENT_MAG_THRESHOLD = 4.5


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _quantize(value: float, step: float) -> float:
    import math
    return math.floor(value / step) * step


def derive_spatial_key(event: dict) -> str:
    # En esta fase se prioriza lat/lon para evitar que un region_code amplio
    # comprima demasiados eventos en muy pocas claves espaciales.
    lat = event.get("latitude")
    lon = event.get("longitude")
    if lat is not None and lon is not None:
        lat_bin = _quantize(float(lat), SPATIAL_BIN_DEGREES)
        lon_bin = _quantize(float(lon), SPATIAL_BIN_DEGREES)
        return f"bin_{lat_bin:.1f}_{lon_bin:.1f}"

    municipality_code = event.get("municipality_code")
    if municipality_code not in (None, ""):
        return f"mun_{municipality_code}"

    region_code = event.get("region_code")
    if region_code not in (None, ""):
        return str(region_code)

    return "bin_unknown"


def build_region_feature_rows(
    events: list[dict],
    window_spec: str,
    feature_set_version: str,
    feature_generation_id: str,
) -> list[RegionFeatureRow]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for event in events:
        grouped[derive_spatial_key(event)].append(event)

    rows: list[RegionFeatureRow] = []

    for spatial_key, group_events in grouped.items():
        group_events = sorted(group_events, key=lambda e: e["occurred_at_utc"])
        windows = generate_sliding_windows(group_events, window_spec=window_spec, step_days=7)

        for win in windows:
            history = [
                e for e in group_events
                if win["window_start_utc"] <= e["occurred_at_utc"] <= win["window_end_utc"]
            ]
            future = [
                e for e in group_events
                if win["future_start_utc"] < e["occurred_at_utc"] <= win["future_end_utc"]
            ]

            if not history:
                continue

            mags = [float(e["magnitude_value"]) for e in history if e.get("magnitude_value") is not None]
            depths = [float(e["depth_km"]) for e in history if e.get("depth_km") is not None]
            dates = [_parse_dt(e["occurred_at_utc"]) for e in history]
            last_event = max(dates)
            ref_end = _parse_dt(win["window_end_utc"])
            days_since_last_event = (ref_end - last_event).total_seconds() / 86400.0

            # Mitigación mínima del desbalance:
            # una fila es positiva solo si en la ventana futura ocurre al menos un evento >= 4.5
            target_label = 1.0 if any(
                (e.get("magnitude_value") is not None and float(e["magnitude_value"]) >= FUTURE_EVENT_MAG_THRESHOLD)
                for e in future
            ) else 0.0

            rows.append(
                RegionFeatureRow(
                    feature_row_id=build_feature_row_id(
                        feature_set_version=feature_set_version,
                        region_code=spatial_key,
                        window_start_utc=win["window_start_utc"],
                        window_end_utc=win["window_end_utc"],
                    ),
                    feature_generation_id=feature_generation_id,
                    feature_set_version=feature_set_version,
                    region_code=spatial_key,
                    window_start_utc=win["window_start_utc"],
                    window_end_utc=win["window_end_utc"],
                    event_count=len(history),
                    max_magnitude=max(mags) if mags else None,
                    mean_magnitude=mean(mags) if mags else None,
                    mean_depth_km=mean(depths) if depths else None,
                    days_since_last_event=days_since_last_event,
                    target_label=target_label,
                    created_at_utc=utc_now_iso(),
                )
            )

    return rows
