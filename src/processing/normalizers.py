from __future__ import annotations

from datetime import datetime, timezone

from src.ingestion.models import RawRecordEnvelope
from src.processing.models import CandidateEvent


def _to_iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_timestamp(raw_value) -> str | None:
    if raw_value is None:
        return None

    text = str(raw_value).strip()
    if not text:
        return None

    candidates = [
        text,
        text.replace("Z", "+00:00"),
        text.replace("/", "-"),
    ]
    for candidate in candidates:
        try:
            dt = datetime.fromisoformat(candidate)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return _to_iso_utc(dt)
        except Exception:
            continue
    return None


def normalize_coordinates(lat_raw, lon_raw) -> tuple[float | None, float | None]:
    try:
        lat = float(lat_raw)
        lon = float(lon_raw)
    except Exception:
        return None, None

    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return None, None
    return lat, lon


def normalize_depth(depth_raw) -> float | None:
    if depth_raw in (None, ""):
        return None
    try:
        value = float(depth_raw)
    except Exception:
        return None
    return value if value >= 0 else None


def normalize_magnitude(mag_raw, mag_type_raw) -> tuple[float | None, str | None]:
    mag = None
    if mag_raw not in (None, ""):
        try:
            mag = float(mag_raw)
        except Exception:
            mag = None

    mag_type = None
    if mag_type_raw not in (None, ""):
        mag_type = str(mag_type_raw).strip() or None

    return mag, mag_type


def build_candidate_event(raw_record: RawRecordEnvelope) -> CandidateEvent:
    """
    Normalize a raw ingestion record into a candidate event structure.
    Compatible with both object envelopes and dict envelopes.
    """

    # --- compatibility layer ---
    if hasattr(raw_record, "raw_payload"):
        payload = raw_record.raw_payload
        source_id = raw_record.source_id
        ingest_batch_id = raw_record.ingest_batch_id
        raw_asset_id = raw_record.raw_asset_id
        source_event_key = raw_record.source_event_key

    elif isinstance(raw_record, dict):
        payload = raw_record.get("raw_payload", raw_record)
        source_id = raw_record.get("source_id")
        ingest_batch_id = raw_record.get("ingest_batch_id")
        raw_asset_id = raw_record.get("raw_asset_id")
        source_event_key = raw_record.get("source_event_key")

    else:
        raise RuntimeError(f"Unsupported raw_record type: {type(raw_record)}")

    # --- normalization ---
    timestamp = normalize_timestamp(
        payload.get("time")
        or payload.get("datetime")
        or payload.get("fecha_hora")
        or payload.get("occurred_at_utc")
    )

    latitude, longitude = normalize_coordinates(
        payload.get("latitude") or payload.get("lat"),
        payload.get("longitude") or payload.get("lon") or payload.get("lng"),
    )

    depth_km = normalize_depth(
        payload.get("depth") or payload.get("depth_km")
    )

    magnitude_value, magnitude_type = normalize_magnitude(
        payload.get("magnitude") or payload.get("mag"),
        payload.get("magnitude_type") or payload.get("mag_type"),
    )

    region_code = payload.get("region_code")
    municipality_code = payload.get("municipality_code")

    if region_code not in (None, ""):
        region_code = str(region_code).strip() or None
    else:
        region_code = None

    if municipality_code not in (None, ""):
        municipality_code = str(municipality_code).strip() or None
    else:
        municipality_code = None

    return CandidateEvent(
        source_id=source_id,
        ingest_batch_id=ingest_batch_id,
        raw_asset_id=raw_asset_id,
        source_event_key=source_event_key,
        occurred_at_utc=timestamp,
        latitude=latitude,
        longitude=longitude,
        depth_km=depth_km,
        magnitude_value=magnitude_value,
        magnitude_type=magnitude_type,
        region_code=region_code,
        municipality_code=municipality_code,
        raw_payload=payload,
    )