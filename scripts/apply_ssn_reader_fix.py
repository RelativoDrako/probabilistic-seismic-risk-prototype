from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

READER_CONTENT = """from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterator


def _normalize_key(name: str) -> str:
    return str(name).replace("\\ufeff", "").strip().lower()


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


def _iter_csv(csv_path: Path) -> Iterator[dict]:
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
    **_: object,
) -> Iterator[dict]:
    if raw_file is not None:
        csv_path = Path(raw_file)
        if not csv_path.exists():
            raise FileNotFoundError(f"Raw file not found: {csv_path}")
        yield from _iter_csv(csv_path)
        return

    if raw_input_dir is None:
        raise ValueError("Either raw_input_dir or raw_file must be provided")

    raw_dir = Path(raw_input_dir)
    csv_files = sorted(raw_dir.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in: {raw_dir}")

    for csv_path in csv_files:
        yield from _iter_csv(csv_path)
"""

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Apply ssn_reader.py fix atomically.")
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    path = repo_root / "src" / "ingestion" / "readers" / "ssn_reader.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(READER_CONTENT, encoding="utf-8")

    sha = hashlib.sha256(READER_CONTENT.encode("utf-8")).hexdigest()
    print(f"[ok] wrote={path}")
    print(f"[ok] sha256={sha}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
