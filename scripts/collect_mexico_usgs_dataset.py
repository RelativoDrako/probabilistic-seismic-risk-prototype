from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
import requests

USGS_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"

MEXICO_BBOX = {
    "minlatitude": 14.0,
    "maxlatitude": 33.5,
    "minlongitude": -118.5,
    "maxlongitude": -86.0,
}

def iso_now():
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Collect Mexico-only USGS dataset with immutable output.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--starttime", required=True)
    parser.add_argument("--endtime", required=True)
    parser.add_argument("--minmagnitude", type=float, default=2.5)
    parser.add_argument("--limit", type=int, default=5000)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    out_dir = repo_root / "data" / "raw" / "usgs_demo_input"
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = iso_now()
    csv_path = out_dir / f"usgs_mexico_events_{stamp}.csv"
    manifest_path = out_dir / f"usgs_mexico_events_{stamp}.manifest.json"

    params = {
        "format": "geojson",
        "starttime": args.starttime,
        "endtime": args.endtime,
        "minmagnitude": args.minmagnitude,
        "limit": args.limit,
        **MEXICO_BBOX,
    }

    resp = requests.get(USGS_API, params=params, timeout=60)
    resp.raise_for_status()
    payload = resp.json()

    rows = []
    for f in payload.get("features", []):
        props = f.get("properties", {})
        geom = f.get("geometry", {})
        coords = geom.get("coordinates") or [None, None, None]
        ts = props.get("time")
        time_iso = None
        if ts is not None:
            time_iso = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()

        rows.append({
            "event_id": f.get("id"),
            "time": time_iso,
            "latitude": coords[1] if len(coords) > 1 else None,
            "longitude": coords[0] if len(coords) > 0 else None,
            "depth": coords[2] if len(coords) > 2 else None,
            "magnitude": props.get("mag"),
            "mag_type": props.get("magType", "unknown"),
        })

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["event_id", "time", "latitude", "longitude", "depth", "magnitude", "mag_type"],
        )
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "source": "USGS Earthquake API",
        "query": params,
        "records": len(rows),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "csv_path": str(csv_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"[ok] csv_path={csv_path}")
    print(f"[ok] manifest_path={manifest_path}")
    print(f"[ok] records={len(rows)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
