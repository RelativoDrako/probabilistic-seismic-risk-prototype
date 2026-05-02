from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SourceDefinition:
    source_id: str
    source_name: str
    source_kind: str
    provider: str
    source_url: str | None = None
    license_note: str | None = None
    country_scope: str = "MX"
    is_active: int = 1


@dataclass(frozen=True)
class RawFileDescriptor:
    source_id: str
    ingest_batch_id: str
    absolute_path: Path
    relative_path: str
    file_name: str
    content_sha256: str
    file_size_bytes: int
    content_type: str | None
    downloaded_at_utc: str
    source_published_at_utc: str | None = None


@dataclass(frozen=True)
class IngestBatchRecord:
    ingest_batch_id: str
    source_id: str
    batch_label: str
    source_snapshot_ref: str | None
    ingest_mode: str
    started_at_utc: str
    completed_at_utc: str | None
    status: str
    raw_file_count: int
    notes: str | None = None


@dataclass(frozen=True)
class RawRecordEnvelope:
    source_id: str
    ingest_batch_id: str
    raw_asset_id: str
    source_event_key: str | None
    raw_payload: dict[str, Any]
    raw_observed_at_utc: str
