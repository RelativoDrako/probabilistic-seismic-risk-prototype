from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterator


def _normalize_key(name: str) -> str:
    return str(name).replace("\ufeff", "").strip().lower()


def _normalize_row(row: dict) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in row.items():
        nkey = _normalize_key(key)
        normalized[nkey] = "" if value is None else str(value).strip()
    return normalized


def pick(row: dict[str, str], *names: str, default: str = "") -> str:
    for name in names:
        key = _normalize_key(name)
        if key in row and row[key] != "":
            return row[key]
    if default != "":
        return default
    raise KeyError(names)


def _iter_csv(
    csv_path: Path,
    source_id: str | None = None,
    ingest_batch_id: str | None = None,
    raw_asset_id: str | None = None,
) -> Iterator[dict]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)

        for raw_row in reader:
            row = _normalize_row(raw_row)

            source_event_key = pick(
                row,
                "event_id",
                "id",
                "eventid",
                "source_event_key",
                default=csv_path.stem,
            )

            occurred_at_utc = pick(
                row,
                "time",
                "occurred_at_utc",
                "origin_time",
                "datetime",
                default="1970-01-01T00:00:00Z",
            )

            latitude = float(pick(row, "latitude", "lat", default="0"))
            longitude = float(pick(row, "longitude", "lon", "lng", default="0"))
            depth_km = float(pick(row, "depth", "depth_km", default="0"))
            magnitude_value = float(pick(row, "magnitude", "mag", default="0"))
            magnitude_type = pick(row, "mag_type", "magnitude_type", default="unknown")

            yield {
                "source_id": source_id,
                "ingest_batch_id": ingest_batch_id,
                "raw_asset_id": raw_asset_id,
                "source_event_key": source_event_key,
                "occurred_at_utc": occurred_at_utc,
                "latitude": latitude,
                "longitude": longitude,
                "depth_km": depth_km,
                "magnitude_value": magnitude_value,
                "magnitude_type": magnitude_type,
                "raw_payload": row,
                "raw_file_name": csv_path.name,
            }


def read_records(
    raw_input_dir: str | Path | None = None,
    raw_file: str | Path | None = None,
    source_id: str | None = None,
    ingest_batch_id: str | None = None,
    raw_asset_id: str | None = None,
    **_: object,
) -> Iterator[dict]:
    if raw_file is not None:
        csv_path = Path(raw_file)
        if not csv_path.exists():
            raise FileNotFoundError(f"Raw file not found: {csv_path}")
        yield from _iter_csv(
            csv_path,
            source_id=source_id,
            ingest_batch_id=ingest_batch_id,
            raw_asset_id=raw_asset_id,
        )
        return

    if raw_input_dir is None:
        raise ValueError("Either raw_input_dir or raw_file must be provided")

    raw_dir = Path(raw_input_dir)
    csv_files = sorted(raw_dir.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in: {raw_dir}")

    for csv_path in csv_files:
        yield from _iter_csv(
            csv_path,
            source_id=source_id,
            ingest_batch_id=ingest_batch_id,
            raw_asset_id=raw_asset_id,
        )
