from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

RAW_JSONL = Path("data/raw/ssn_demo_input/ssn_raw_events.jsonl")
OUT_CSV = Path("data/raw/ssn_demo_input/ssn_demo_events.csv")
OUT_MANIFEST = Path("data/raw/ssn_demo_input/dataset_manifest.json")


def safe_float(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(str(value).strip())
    except Exception:
        return None


def normalize_row(record: dict[str, Any]) -> dict[str, Any] | None:
    payload = record.get("raw_payload", {})
    event_id = record.get("source_event_key")
    timestamp = payload.get("time")
    latitude = safe_float(payload.get("lat") or payload.get("latitude"))
    longitude = safe_float(payload.get("lon") or payload.get("lng") or payload.get("longitude"))
    depth = safe_float(payload.get("depth") or payload.get("depth_km"))
    magnitude = safe_float(payload.get("mag") or payload.get("magnitude"))
    mag_type = payload.get("mag_type") or payload.get("magnitude_type") or "unknown"

    if not event_id or not timestamp:
        return None
    if latitude is None or longitude is None:
        return None

    return {
        "event_id": event_id,
        "time": timestamp,
        "latitude": latitude,
        "longitude": longitude,
        "depth": depth if depth is not None else 0.0,
        "magnitude": magnitude if magnitude is not None else 0.0,
        "mag_type": mag_type,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build reproducible demo CSV from real SSN raw snapshot.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--max-records", type=int, default=3000)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    raw_jsonl_path = repo_root / RAW_JSONL
    out_csv_path = repo_root / OUT_CSV
    manifest_path = repo_root / OUT_MANIFEST

    if not raw_jsonl_path.exists():
        raise FileNotFoundError(f"Raw JSONL not found: {raw_jsonl_path}")

    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    with raw_jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            normalized = normalize_row(record)
            if normalized is None:
                continue
            if normalized["event_id"] in seen_ids:
                continue
            seen_ids.add(normalized["event_id"])
            rows.append(normalized)
            if len(rows) >= args.max_records:
                break

    out_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with out_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["event_id", "time", "latitude", "longitude", "depth", "magnitude", "mag_type"],
        )
        writer.writeheader()
        writer.writerows(rows)

    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}

    manifest.update({
        "demo_csv_file": out_csv_path.name,
        "demo_record_count": len(rows),
        "build_notes": "Demo snapshot derived from real SSN raw evidence.",
    })
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[ok] demo_csv={out_csv_path}")
    print(f"[ok] demo_record_count={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())