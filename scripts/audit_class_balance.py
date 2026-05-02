from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path

from src.common.target_contract import TARGET_DEFINITION


MAG_BINS = [
    (2.5, 3.0),
    (3.0, 3.5),
    (3.5, 4.0),
    (4.0, 4.5),
    (4.5, 5.0),
    (5.0, None),
]


def _bucketize(values: list[float]) -> dict[str, int]:
    result: dict[str, int] = {}
    for lo, hi in MAG_BINS:
        if hi is None:
            label = f"{lo}+"
            count = sum(1 for v in values if v >= lo)
        else:
            label = f"{lo}-{hi}"
            count = sum(1 for v in values if lo <= v < hi)
        result[label] = count
    return result


def _resolve_raw_file_path(repo_root: Path, relative_path: str) -> Path | None:
    raw_root = repo_root / "data" / "raw"
    rel_path = Path(relative_path)

    direct = raw_root / rel_path
    if direct.exists() and direct.is_file():
        return direct

    matches: list[Path] = []
    for candidate in raw_root.rglob(rel_path.name):
        if not candidate.is_file():
            continue
        if "_meta" in candidate.parts:
            continue
        matches.append(candidate)

    if len(matches) == 1:
        return matches[0]

    rel_suffix = rel_path.as_posix()
    for candidate in matches:
        candidate_rel = candidate.relative_to(raw_root).as_posix()
        if candidate_rel.endswith(rel_suffix):
            return candidate

    return None


def _read_raw_magnitudes(csv_path: Path) -> tuple[int, list[float], int]:
    total_rows = 0
    mags: list[float] = []
    null_mag_rows = 0

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_rows += 1
            raw_mag = row.get("magnitude") or row.get("mag")
            if raw_mag in (None, ""):
                null_mag_rows += 1
                continue
            try:
                mags.append(float(raw_mag))
            except Exception:
                null_mag_rows += 1

    return total_rows, mags, null_mag_rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Audit class balance and magnitude preservation.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--ingest-batch-id", required=True)
    parser.add_argument("--feature-set-version", required=True)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    db_path = repo_root / "artifacts" / "sqlite" / "seismic_prototype.db"
    reports_dir = repo_root / "artifacts" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        raw_assets = conn.execute(
            """
            SELECT relative_path
            FROM raw_asset_manifest
            WHERE ingest_batch_id = ?
            ORDER BY relative_path
            """,
            (args.ingest_batch_id,),
        ).fetchall()

        raw_csv_paths: list[Path] = []
        for asset in raw_assets:
            relative_path = asset["relative_path"]
            if Path(relative_path).suffix.lower() != ".csv":
                continue
            resolved = _resolve_raw_file_path(repo_root, relative_path)
            if resolved is not None:
                raw_csv_paths.append(resolved)

        raw_total = 0
        raw_null_mag_rows = 0
        raw_mags: list[float] = []
        for csv_path in raw_csv_paths:
            total_rows, mags, null_mag_rows = _read_raw_magnitudes(csv_path)
            raw_total += total_rows
            raw_null_mag_rows += null_mag_rows
            raw_mags.extend(mags)

        curated = conn.execute(
            """
            SELECT magnitude_value
            FROM curated_events
            WHERE ingest_batch_id = ? AND record_status = 'accepted'
            """,
            (args.ingest_batch_id,),
        ).fetchall()
        curated_mags = [float(r["magnitude_value"]) for r in curated if r["magnitude_value"] is not None]

        feature_generation = conn.execute(
            """
            SELECT feature_generation_id
            FROM feature_generations
            WHERE source_batch_scope = ? AND feature_set_version = ?
            ORDER BY started_at_utc DESC
            LIMIT 1
            """,
            (args.ingest_batch_id, args.feature_set_version),
        ).fetchone()
        feature_generation_id = feature_generation["feature_generation_id"] if feature_generation else None

        feature_rows = []
        if feature_generation_id:
            feature_rows = conn.execute(
                """
                SELECT target_label
                FROM region_features
                WHERE feature_generation_id = ?
                """,
                (feature_generation_id,),
            ).fetchall()
    finally:
        conn.close()

    positives = sum(1 for r in feature_rows if int(r["target_label"] or 0) == 1)
    negatives = sum(1 for r in feature_rows if int(r["target_label"] or 0) == 0)
    row_count = len(feature_rows)

    payload = {
        "ingest_batch_id": args.ingest_batch_id,
        "feature_set_version": args.feature_set_version,
        "feature_generation_id": feature_generation_id,
        "target_definition": TARGET_DEFINITION,
        "raw_files_count": len(raw_csv_paths),
        "raw_rows": raw_total,
        "raw_null_magnitude_rows": raw_null_mag_rows,
        "raw_magnitude_bins": _bucketize(raw_mags),
        "max_raw_magnitude": max(raw_mags) if raw_mags else None,
        "curated_rows": len(curated_mags),
        "curated_null_magnitude_rows": max(len(curated) - len(curated_mags), 0),
        "curated_magnitude_bins": _bucketize(curated_mags),
        "max_curated_magnitude": max(curated_mags) if curated_mags else None,
        "positive_labels": positives,
        "negative_labels": negatives,
        "positive_ratio": (positives / row_count) if row_count else 0.0,
        "negative_ratio": (negatives / row_count) if row_count else 0.0,
        "threshold_sensitivity_reference": {
            "3.5": "manual sensitivity analysis recommended",
            "4.0": "manual sensitivity analysis recommended",
            "4.5": "canonical target threshold",
            "5.0": "manual sensitivity analysis recommended",
        },
    }

    json_path = reports_dir / "class_balance_audit.json"
    md_path = reports_dir / "class_balance_audit.md"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_lines = [
        "# Class balance audit",
        "",
        f"- ingest_batch_id: `{args.ingest_batch_id}`",
        f"- feature_generation_id: `{feature_generation_id}`",
        f"- target_definition: `{TARGET_DEFINITION}`",
        f"- raw_files_count: `{payload['raw_files_count']}`",
        f"- raw_rows: `{payload['raw_rows']}`",
        f"- curated_rows: `{payload['curated_rows']}`",
        f"- positive_labels: `{positives}`",
        f"- negative_labels: `{negatives}`",
        f"- positive_ratio: `{payload['positive_ratio']:.6f}`",
        f"- negative_ratio: `{payload['negative_ratio']:.6f}`",
        "",
        "## Raw magnitude bins",
    ]
    for label, value in payload["raw_magnitude_bins"].items():
        md_lines.append(f"- {label}: {value}")

    md_lines.extend([
        "",
        "## Curated magnitude bins",
    ])
    for label, value in payload["curated_magnitude_bins"].items():
        md_lines.append(f"- {label}: {value}")

    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"[ok] class_balance_audit_json={json_path.as_posix()}")
    print(f"[ok] class_balance_audit_md={md_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
