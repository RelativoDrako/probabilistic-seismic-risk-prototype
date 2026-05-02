from __future__ import annotations

import csv
from pathlib import Path


def pick(row, *names):
    for n in names:
        if n in row:
            return row[n]
    raise KeyError(names)


def read_records(*, raw_file: Path, source_id: str, ingest_batch_id: str, raw_asset_id: str):

    with open(raw_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:

            event = {
                "source_event_key": pick(row, "event_id", "id"),
                "occurred_at_utc": pick(row, "time", "timestamp"),
                "latitude": float(pick(row, "latitude", "lat")),
                "longitude": float(pick(row, "longitude", "lon")),
                "depth_km": float(pick(row, "depth", "depth_km")),
                "magnitude_value": float(pick(row, "magnitude", "mag")),
                "magnitude_type": pick(row, "mag_type", "type"),
            }

            metadata = {
                "source_id": source_id,
                "ingest_batch_id": ingest_batch_id,
                "raw_asset_id": raw_asset_id,
            }

            yield {
                "event": event,
                "metadata": metadata,
            }