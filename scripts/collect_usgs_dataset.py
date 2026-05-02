from __future__ import annotations

import argparse
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta, timezone
import requests


USGS_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"


def fetch_events(days: int = 365, min_magnitude: float = 3.0):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    params = {
        "format": "geojson",
        "starttime": start.date().isoformat(),
        "endtime": end.date().isoformat(),
        "minmagnitude": min_magnitude,
        "limit": 20000,
    }

    try:
        r = requests.get(USGS_API, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        print(f"[error] request failed: {e}")
        return []

    return data.get("features", [])


def normalize(feature):
    props = feature.get("properties", {})
    geometry = feature.get("geometry") or {}
    coords = geometry.get("coordinates") or [None, None, None]

    timestamp = props.get("time")
    if timestamp is not None:
        time_iso = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).isoformat()
    else:
        time_iso = None

    return {
        "event_id": feature.get("id"),
        "time": time_iso,
        "latitude": coords[1] if len(coords) > 1 else None,
        "longitude": coords[0] if len(coords) > 0 else None,
        "depth": coords[2] if len(coords) > 2 else None,
        "magnitude": props.get("mag") or 0.0,
        "mag_type": props.get("magType", "unknown"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--target-size", type=int, default=3000)

    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    if not repo_root.exists():
        raise ValueError(f"Repo root does not exist: {repo_root}")

    raw_dir = repo_root / "data/raw/ssn_demo_input"
    raw_dir.mkdir(parents=True, exist_ok=True)

    csv_path = raw_dir / "ssn_demo_events.csv"
    manifest_path = raw_dir / "dataset_manifest.json"

    print("[info] downloading USGS dataset...")

    features = fetch_events()

    rows = [normalize(f) for f in features if f]
    rows = rows[:args.target_size]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "event_id",
                "time",
                "latitude",
                "longitude",
                "depth",
                "magnitude",
                "mag_type",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "source": "USGS Earthquake API",
        "url": USGS_API,
        "records": len(rows),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"[ok] dataset generated: {csv_path}")
    print(f"[ok] records: {len(rows)}")


if __name__ == "__main__":
    main()