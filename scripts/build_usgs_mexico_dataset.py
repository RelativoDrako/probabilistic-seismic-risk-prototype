from __future__ import annotations

import argparse
import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

USGS_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"

MEXICO_BBOX = {
    "minlatitude": 14.0,
    "maxlatitude": 33.0,
    "minlongitude": -118.0,
    "maxlongitude": -86.0,
}

CSV_FIELDS = [
    "time",
    "latitude",
    "longitude",
    "depth",
    "mag",
    "magType",
    "place",
    "gap",
    "dmin",
    "rms",
    "horizontalError",
    "depthError",
    "magError",
    "id",
]


def _utc_today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _iter_year_ranges(start_year: int, end_date: str):
    end_year = int(end_date[:4])
    for year in range(start_year, end_year + 1):
        start = f"{year}-01-01"
        end = end_date if year == end_year else f"{year}-12-31"
        yield year, start, end


def _request_year_csv(start: str, end: str, min_mag: float, timeout: int = 120) -> str:
    params = {
        "format": "csv",
        "starttime": start,
        "endtime": end,
        "minmagnitude": min_mag,
        "orderby": "time-asc",
        "limit": 20000,
        "eventtype": "earthquake",
        **MEXICO_BBOX,
    }

    resp = requests.get(USGS_API, params=params, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"USGS API request failed: HTTP {resp.status_code} for range {start}..{end}")
    return resp.text


def _read_csv_text(csv_text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(csv_text)))


def _normalize_row(row: dict) -> dict | None:
    if not row.get("time") or not row.get("latitude") or not row.get("longitude") or not row.get("mag"):
        return None

    normalized = {k: row.get(k, "") for k in CSV_FIELDS}
    return normalized


def _dedupe_rows(rows: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for row in rows:
        key = (
            row.get("time"),
            row.get("latitude"),
            row.get("longitude"),
            row.get("mag"),
            row.get("id"),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def build_dataset(repo_root: Path, start_year: int, min_mag: float, force: bool = False) -> tuple[Path, Path, int]:
    out_dir = repo_root / "data" / "raw" / "usgs_mexico_catalog"
    out_dir.mkdir(parents=True, exist_ok=True)

    end_date = _utc_today_iso()
    dataset_name = f"usgs_mexico_catalog_{start_year}_{end_date[:4]}.csv"
    csv_path = out_dir / dataset_name
    manifest_path = out_dir / f"{dataset_name}.manifest.json"

    if csv_path.exists() and manifest_path.exists() and not force:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        print(f"[skip] dataset already exists: {csv_path}")
        print(f"[ok] records={manifest.get('records')}")
        return csv_path, manifest_path, int(manifest.get("records", 0))

    all_rows = []
    yearly_stats = []

    for year, start, end in _iter_year_ranges(start_year, end_date):
        print(f"[info] requesting year={year} range={start}..{end}")
        csv_text = _request_year_csv(start=start, end=end, min_mag=min_mag)
        raw_rows = _read_csv_text(csv_text)
        norm_rows = [r for r in (_normalize_row(x) for x in raw_rows) if r is not None]
        yearly_stats.append({"year": year, "rows": len(norm_rows)})
        all_rows.extend(norm_rows)

    deduped = _dedupe_rows(all_rows)

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(deduped)

    manifest = {
        "source": "USGS Earthquake Catalog API",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "start_year": start_year,
        "end_date": end_date,
        "min_magnitude": min_mag,
        "bbox": MEXICO_BBOX,
        "records": len(deduped),
        "yearly_stats": yearly_stats,
        "csv_path": str(csv_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"[ok] csv_path={csv_path}")
    print(f"[ok] manifest_path={manifest_path}")
    print(f"[ok] records={len(deduped)}")
    return csv_path, manifest_path, len(deduped)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build canonical USGS Mexico dataset with yearly chunking.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--start-year", type=int, default=2005)
    parser.add_argument("--min-mag", type=float, default=2.5)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    build_dataset(repo_root=repo_root, start_year=args.start_year, min_mag=args.min_mag, force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
