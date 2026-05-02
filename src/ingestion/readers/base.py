from __future__ import annotations

from pathlib import Path
from typing import Iterable, Protocol

from src.ingestion.models import RawRecordEnvelope


class RawReader(Protocol):
    def read_records(
        self,
        raw_file: Path,
        source_id: str,
        ingest_batch_id: str,
        raw_asset_id: str,
    ) -> Iterable[RawRecordEnvelope]:
        ...
