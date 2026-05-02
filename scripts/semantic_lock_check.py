from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def parse_key_values(text: str, keys: list[str]) -> dict[str, str]:
    data = {}
    for key in keys:
        pattern = rf"(?:^|- )\s*{re.escape(key)}:\s*(.+)"
        match = re.search(pattern, text, flags=re.MULTILINE)
        if match:
            data[key] = match.group(1).strip()
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check semantic lock consistency across reports.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    metrics_path = repo_root / "artifacts" / "reports" / "metrics.json"
    summary_path = repo_root / "artifacts" / "reports" / "evaluation_summary.md"
    demo_path = repo_root / "artifacts" / "reports" / "demo_evidence.md"

    if not metrics_path.exists() or not summary_path.exists() or not demo_path.exists():
        print("[error] one or more required report files are missing")
        return 2

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    summary = parse_key_values(summary_path.read_text(encoding="utf-8"), [
        "model", "ingest_batch_id", "feature_set_version", "split_rule", "target_definition"
    ])
    demo = parse_key_values(demo_path.read_text(encoding="utf-8"), [
        "ingest_batch_id", "feature_set_version", "model", "split_rule", "target_definition"
    ])

    checks = {
        "ingest_batch_id": (
            str(metrics.get("ingest_batch_id", "")),
            str(summary.get("ingest_batch_id", "")),
            str(demo.get("ingest_batch_id", "")),
        ),
        "feature_set_version": (
            str(metrics.get("feature_set_version", "")),
            str(summary.get("feature_set_version", "")),
            str(demo.get("feature_set_version", "")),
        ),
        "model": (
            str(metrics.get("model", "")),
            str(summary.get("model", "")),
            str(demo.get("model", metrics.get("model", ""))),
        ),
        "target_definition": (
            str(metrics.get("target_definition", "")),
            str(summary.get("target_definition", "")),
            str(demo.get("target_definition", metrics.get("target_definition", ""))),
        ),
        "split_rule": (
            str(metrics.get("split_rule", "")),
            str(summary.get("split_rule", "")),
            str(demo.get("split_rule", metrics.get("split_rule", ""))),
        ),
    }

    failed = []
    for key, values in checks.items():
        normalized = [v for v in values if v != ""]
        if len(set(normalized)) > 1:
            failed.append((key, values))

    logs_dir = repo_root / "_ops_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    status = {"semantic_lock_status": "PASS" if not failed else "FAIL", "checks": checks, "failed": failed}
    (logs_dir / "semantic_lock_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")

    if failed:
        print("[error] semantic lock mismatch detected")
        for key, values in failed:
            print(f"  - {key}: {values}")
        return 1 if args.strict else 0

    print("[ok] semantic lock consistent")
    for key, values in checks.items():
        print(f"[ok] {key}={values[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
