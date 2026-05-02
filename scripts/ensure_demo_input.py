from __future__ import annotations

import argparse
import csv
from pathlib import Path

DEMO_ROWS = [
    ("ev001", "2026-03-01T10:15:00Z", 19.4326, -99.1332, 12.4, 4.1, "Mw"),
    ("ev002", "2026-03-02T03:20:00Z", 16.8531, -99.8237, 18.1, 4.8, "Mw"),
    ("ev003", "2026-03-03T18:42:00Z", 24.1426, -110.3128, 9.6, 3.9, "Ml"),
    ("ev004", "2026-03-04T07:05:00Z", 20.6597, -103.3496, 22.0, 4.3, "Mw"),
    ("ev005", "2026-03-05T11:55:00Z", 17.0732, -96.7266, 31.2, 5.0, "Mw"),
    ("ev006", "2026-03-06T21:11:00Z", 25.6866, -100.3161, 14.0, 3.7, "Ml"),
]

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ensure a minimal local demo dataset exists.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--raw-input-dir", default="data/raw/ssn_demo_input")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    raw_dir = repo_root / args.raw_input_dir
    raw_dir.mkdir(parents=True, exist_ok=True)

    csv_path = raw_dir / "ssn_demo_events.csv"
    if csv_path.exists():
        print(f"[ok] dataset already exists: {csv_path}")
        return 0

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["event_id", "time", "latitude", "longitude", "depth", "magnitude", "mag_type"])
        writer.writerows(DEMO_ROWS)

    print(f"[ok] demo dataset generated: {csv_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
