from __future__ import annotations

import argparse
import csv
from pathlib import Path

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Basic dataset sufficiency gate.")
    parser.add_argument("--csv-path", required=True)
    parser.add_argument("--min-rows", type=int, default=200)
    parser.add_argument("--min-distinct-latlon", type=int, default=20)
    args = parser.parse_args(argv)

    csv_path = Path(args.csv_path)
    rows = list(csv.DictReader(csv_path.open("r", encoding="utf-8")))
    distinct_points = {(r.get("latitude"), r.get("longitude")) for r in rows if r.get("latitude") and r.get("longitude")}

    if len(rows) < args.min_rows:
        print(f"[error] insufficient_rows={len(rows)} min_required={args.min_rows}")
        return 2
    if len(distinct_points) < args.min_distinct_latlon:
        print(f"[error] insufficient_distinct_points={len(distinct_points)} min_required={args.min_distinct_latlon}")
        return 3

    print(f"[ok] rows={len(rows)}")
    print(f"[ok] distinct_points={len(distinct_points)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
