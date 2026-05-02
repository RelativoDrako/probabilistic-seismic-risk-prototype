from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Inspect sufficiency of generated feature dataset.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--feature-generation-id", required=True)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    db_path = repo_root / "artifacts" / "sqlite" / "seismic_prototype.db"
    out_path = repo_root / "_ops_logs" / f"feature_sufficiency_{args.feature_generation_id}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM region_features WHERE feature_generation_id = ?",
            (args.feature_generation_id,),
        ).fetchall()
    finally:
        conn.close()

    row_count = len(rows)
    spatial_keys = {r["region_code"] for r in rows if r["region_code"] not in (None, "")}
    positives = sum(1 for r in rows if r["target_label"] not in (None, 0, 0.0))
    negatives = sum(1 for r in rows if r["target_label"] in (0, 0.0))

    positive_ratio = (positives / row_count) if row_count else 0.0
    negative_ratio = (negatives / row_count) if row_count else 0.0

    payload = {
        "feature_generation_id": args.feature_generation_id,
        "row_count": row_count,
        "distinct_spatial_keys": len(spatial_keys),
        "positive_labels": positives,
        "negative_labels": negatives,
        "positive_ratio": positive_ratio,
        "negative_ratio": negative_ratio,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] report={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
