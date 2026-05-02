from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.ssn.unam.mx/sismicidad/ultimos/"
COLLECTOR_VERSION = "v1"
CACHE_TTL_HOURS = 24
DEFAULT_TARGET_SIZE = 3000

LOGGER = logging.getLogger("collect_ssn_dataset")


@dataclass(frozen=True)
class CollectorPaths:
    repo_root: Path
    cache_dir: Path
    raw_dir: Path
    state_path: Path
    raw_jsonl_path: Path
    manifest_path: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_dirs(repo_root: Path) -> CollectorPaths:
    cache_dir = repo_root / "data" / "external_cache" / "ssn_html_cache"
    raw_dir = repo_root / "data" / "raw" / "ssn_demo_input"
    cache_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    return CollectorPaths(
        repo_root=repo_root,
        cache_dir=cache_dir,
        raw_dir=raw_dir,
        state_path=raw_dir / "collector_state.json",
        raw_jsonl_path=raw_dir / "ssn_raw_events.jsonl",
        manifest_path=raw_dir / "dataset_manifest.json",
    )


def load_state(state_path: Path) -> dict[str, Any]:
    if state_path.exists():
        return json.loads(state_path.read_text(encoding="utf-8"))
    return {"seen": [], "last_date": None}


def save_state(state_path: Path, state: dict[str, Any]) -> None:
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def md5_text(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_cache_valid(path: Path) -> bool:
    if not path.exists():
        return False
    age_seconds = time.time() - path.stat().st_mtime
    return age_seconds < CACHE_TTL_HOURS * 3600


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (compatible; seismic-early-detection/1.0; local-first collector)"
    })
    return session


def cached_get(session: requests.Session, cache_dir: Path, url: str) -> str | None:
    cache_path = cache_dir / f"{md5_text(url)}.html"

    if is_cache_valid(cache_path):
        return cache_path.read_text(encoding="utf-8", errors="replace")

    for attempt in range(3):
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            html = resp.text
            if len(html) < 500:
                raise ValueError("Suspiciously short HTML response")
            cache_path.write_text(html, encoding="utf-8")
            return html
        except Exception as exc:
            LOGGER.warning("fetch retry=%s url=%s error=%s", attempt + 1, url, exc)
            time.sleep(2**attempt)

    return None


def safe_float(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(str(value).strip())
    except Exception:
        return None


def parse_html(html: str, day: datetime) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        LOGGER.warning("No table found for day=%s", day.date())
        return []

    rows = table.find_all("tr")[1:]
    results: list[dict[str, Any]] = []

    for row in rows:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) < 6:
            continue

        lat = safe_float(cols[1])
        lon = safe_float(cols[2])
        mag = safe_float(cols[3])
        depth = safe_float(cols[4]) if len(cols) > 4 else None
        region = cols[5] if len(cols) > 5 else None

        event_key = hashlib.sha256(f"{day.date()}|{cols}".encode("utf-8")).hexdigest()[:24]

        results.append({
            "source_id": "ssn",
            "source_event_key": event_key,
            "raw_payload": {
                "time": cols[0],
                "lat": lat,
                "lon": lon,
                "mag": mag,
                "depth": depth,
                "region": region,
            },
            "collector_date": day.date().isoformat(),
            "collector_version": COLLECTOR_VERSION,
            "collected_at_utc": utc_now_iso(),
        })

    return results


def fetch_day(session: requests.Session, cache_dir: Path, day: datetime) -> list[dict[str, Any]]:
    url = f"{BASE_URL}?fecha={day.strftime('%Y-%m-%d')}"
    html = cached_get(session, cache_dir, url)
    if not html:
        return []
    return parse_html(html, day)


def collect_records(paths: CollectorPaths, target_size: int) -> list[dict[str, Any]]:
    state = load_state(paths.state_path)
    seen = set(state.get("seen", []))

    current_day = (
        datetime.fromisoformat(state["last_date"])
        if state.get("last_date")
        else datetime.now(timezone.utc)
    )

    session = build_session()
    results: list[dict[str, Any]] = []

    while len(results) < target_size:
        LOGGER.info("Fetching day=%s", current_day.date())
        daily = fetch_day(session, paths.cache_dir, current_day)

        for record in daily:
            key = record["source_event_key"]
            if key in seen:
                continue
            seen.add(key)
            results.append(record)

        state["seen"] = sorted(seen)
        state["last_date"] = current_day.isoformat()
        save_state(paths.state_path, state)

        current_day -= timedelta(days=1)
        if current_day.year < 2015:
            break
        time.sleep(0.5)

    return results[:target_size]


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def write_manifest(paths: CollectorPaths, record_count: int) -> None:
    manifest = {
        "source_name": "Servicio Sismológico Nacional (SSN UNAM)",
        "source_url": BASE_URL,
        "collector_version": COLLECTOR_VERSION,
        "collected_at_utc": utc_now_iso(),
        "record_count": record_count,
        "raw_jsonl_file": paths.raw_jsonl_path.name,
        "snapshot_hash_sha256": sha256_file(paths.raw_jsonl_path) if paths.raw_jsonl_path.exists() else None,
        "notes": "Raw evidence snapshot for local-first demo dataset generation.",
    }
    paths.manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect real SSN records into raw local evidence.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--target-size", type=int, default=DEFAULT_TARGET_SIZE)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    repo_root = Path(args.repo_root).resolve()
    paths = ensure_dirs(repo_root)

    records = collect_records(paths, args.target_size)
    record_count = write_jsonl(paths.raw_jsonl_path, records)
    write_manifest(paths, record_count)

    print(f"[ok] raw_jsonl={paths.raw_jsonl_path}")
    print(f"[ok] manifest={paths.manifest_path}")
    print(f"[ok] collected_records={record_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())