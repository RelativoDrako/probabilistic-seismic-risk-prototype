from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CandidateEvent:
    source_id: str
    ingest_batch_id: str
    raw_asset_id: str
    source_event_key: str | None
    occurred_at_utc: str | None
    latitude: float | None
    longitude: float | None
    depth_km: float | None
    magnitude_value: float | None
    magnitude_type: str | None
    region_code: str | None
    municipality_code: str | None
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class CuratedEventRecord:
    event_id: str
    source_id: str
    ingest_batch_id: str
    source_event_key: str | None
    occurred_at_utc: str
    latitude: float
    longitude: float
    depth_km: float | None
    magnitude_value: float | None
    magnitude_type: str | None
    region_code: str
    municipality_code: str | None
    curation_version: str
    record_status: str
    raw_asset_id: str
    inserted_at_utc: str
    updated_at_utc: str
    rejection_reason: str | None = None


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: str
