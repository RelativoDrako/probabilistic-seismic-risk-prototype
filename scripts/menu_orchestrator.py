from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

CRITICAL_ARTIFACTS = [
    "artifacts/sqlite/seismic_prototype.db",
    "artifacts/models/baseline_model.joblib",
    "artifacts/reports/metrics.json",
    "artifacts/reports/evaluation_summary.md",
    "artifacts/reports/demo_evidence.md",
    "artifacts/plots/pipeline_trace.png",
    "artifacts/plots/regional_event_counts.png",
    "artifacts/plots/magnitude_distribution.png",
    "artifacts/plots/risk_heatmap.png",
    "artifacts/plots/probabilistic_risk_map.png",
    "artifacts/plots/metrics_panel.png",
    "artifacts/plots/model_summary_panel.png",
]

BASE_SCRIPTS = {
    "apply": "apply_deliverables.py",
    "setup": "setup_env.py",
    "validate": "validate_env.py",
    "orchestrate": "orchestrate_demo.py",
    "semantic": "semantic_lock_check.py",
}

def is_windows_path(text: str) -> bool:
    return len(text) > 2 and text[1] == ":"

def is_posix_path(text: str) -> bool:
    return text.startswith("/")

def preflight(repo_root: Path, workspace_root: Path) -> tuple[bool, list[str]]:
    issues = []
    if not repo_root.exists():
        issues.append(f"repo root missing: {repo_root}")
    if not workspace_root.exists():
        issues.append(f"workspace root missing: {workspace_root}")
    if (is_windows_path(str(repo_root)) and is_posix_path(str(workspace_root))) or (
        is_posix_path(str(repo_root)) and is_windows_path(str(workspace_root))
    ):
        issues.append("mixed path styles detected")
    scripts_dir = repo_root / "scripts"
    required = list(BASE_SCRIPTS.values()) + ["ensure_demo_input.py"]
    for script in required:
        if not (scripts_dir / script).exists():
            issues.append(f"missing base script: scripts/{script}")
    return (len(issues) == 0, issues)

def latest_ids(repo_root: Path) -> tuple[str | None, str | None]:
    db_path = repo_root / "artifacts" / "sqlite" / "seismic_prototype.db"
    if not db_path.exists():
        return None, None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        batch = conn.execute("SELECT ingest_batch_id FROM ingest_batches ORDER BY started_at_utc DESC LIMIT 1").fetchone()
        feat = conn.execute("SELECT feature_generation_id FROM feature_generations ORDER BY started_at_utc DESC LIMIT 1").fetchone()
        return (
            None if batch is None else batch["ingest_batch_id"],
            None if feat is None else feat["feature_generation_id"],
        )
    except Exception:
        return None, None
    finally:
        conn.close()

def latest_status(repo_root: Path) -> str:
    path = repo_root / "_ops_logs" / "orchestrate_demo_report.json"
    if not path.exists():
        return "UNKNOWN"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload.get("run_status", "UNKNOWN")
    except Exception:
        return "UNKNOWN"

def append_run_log(repo_root: Path, entry: dict) -> None:
    logs_dir = repo_root / "_ops_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "menu_run_log.json"
    if log_path.exists():
        try:
            payload = json.loads(log_path.read_text(encoding="utf-8"))
        except Exception:
            payload = []
    else:
        payload = []
    payload.append(entry)
    log_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def run_python(script_path: Path, args: list[str], cwd: Path, dry_run: bool) -> int:
    cmd = [sys.executable, str(script_path), *args]
    if dry_run:
        print(f"[dry-run] {' '.join(cmd)}")
        return 0
    proc = subprocess.run(cmd, cwd=str(cwd), text=True)
    return proc.returncode

def inspect_artifacts(repo_root: Path) -> tuple[list[str], list[str]]:
    existing, missing = [], []
    for rel in CRITICAL_ARTIFACTS:
        if (repo_root / rel).exists():
            existing.append(rel)
        else:
            missing.append(rel)
    return existing, missing

def build_menu_text(repo_root: Path, workspace_root: Path) -> str:
    batch_id, feature_id = latest_ids(repo_root)
    status = latest_status(repo_root)
    return f"""
================ Seismic Demo Menu ================
Repo root:              {repo_root}
Workspace root:         {workspace_root}
Latest ingest batch id: {batch_id or 'N/A'}
Latest feature gen id:  {feature_id or 'N/A'}
Latest run status:      {status}

0. Exit
1. Apply deliverables
2. Setup environment
3. Validate environment
4. Run full pre-demo pipeline
5. Run semantic lock check
6. Serve final HTML locally
7. Inspect critical artifacts
8. Re-run from a selected stage
9. Show latest run status
===================================================
Select option: """.strip("\n")

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Interactive menu orchestrator for the seismic repo.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume-from", choices=["bootstrap", "ensure_demo_input", "ingest", "curate", "features", "train", "evaluate", "visualize"], default=None)
    parser.add_argument("--raw-input-dir", default="data/raw/ssn_demo_input")
    parser.add_argument("--batch-label", default="demo_batch_usgs_001")
    parser.add_argument("--source-id", default="usgs_demo")
    parser.add_argument("--source-name", default="USGS Demo")
    parser.add_argument("--source-kind", default="catalog")
    parser.add_argument("--provider", default="USGS")
    parser.add_argument("--ingest-mode", default="manual")
    parser.add_argument("--curation-version", default="v1")
    parser.add_argument("--feature-set-version", default="v1")
    parser.add_argument("--window-spec", default="30d")
    parser.add_argument("--html-port", type=int, default=8008)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    workspace_root = Path(args.workspace_root).resolve()
    ok, issues = preflight(repo_root, workspace_root)
    if not ok:
        for issue in issues:
            print(f"[error] {issue}")
        return 2

    scripts_dir = repo_root / "scripts"

    while True:
        try:
            choice = input(build_menu_text(repo_root, workspace_root)).strip()
        except KeyboardInterrupt:
            print("\n[info] interrupted by user")
            return 130

        if choice == "0":
            print("[info] exit")
            return 0
        elif choice == "1":
            rc = run_python(
                scripts_dir / BASE_SCRIPTS["apply"],
                ["--repo-root", str(repo_root), "--workspace-root", str(workspace_root), *(["--strict"] if args.strict else []), *(["--dry-run"] if args.dry_run else [])],
                repo_root,
                args.dry_run,
            )
            append_run_log(repo_root, {"action": "apply_deliverables", "returncode": rc})
        elif choice == "2":
            rc = run_python(
                scripts_dir / BASE_SCRIPTS["setup"],
                ["--repo-root", str(repo_root), *(["--dry-run"] if args.dry_run else [])],
                repo_root,
                args.dry_run,
            )
            append_run_log(repo_root, {"action": "setup_env", "returncode": rc})
        elif choice == "3":
            rc = run_python(
                scripts_dir / BASE_SCRIPTS["validate"],
                ["--repo-root", str(repo_root), *(["--strict"] if args.strict else [])],
                repo_root,
                args.dry_run,
            )
            append_run_log(repo_root, {"action": "validate_env", "returncode": rc})
        elif choice == "4":
            rc = run_python(
                scripts_dir / BASE_SCRIPTS["orchestrate"],
                [
                    "--repo-root", str(repo_root),
                    "--source-id", args.source_id,
                    "--source-name", args.source_name,
                    "--source-kind", args.source_kind,
                    "--provider", args.provider,
                    "--raw-input-dir", args.raw_input_dir,
                    "--batch-label", args.batch_label,
                    "--ingest-mode", args.ingest_mode,
                    "--curation-version", args.curation_version,
                    "--feature-set-version", args.feature_set_version,
                    "--window-spec", args.window_spec,
                    *(["--strict"] if args.strict else []),
                    *(["--dry-run"] if args.dry_run else []),
                    *(["--resume-from", args.resume_from] if args.resume_from else []),
                ],
                repo_root,
                args.dry_run,
            )
            append_run_log(repo_root, {"action": "orchestrate_demo", "returncode": rc})
        elif choice == "5":
            rc = run_python(
                scripts_dir / BASE_SCRIPTS["semantic"],
                ["--repo-root", str(repo_root), *(["--strict"] if args.strict else [])],
                repo_root,
                args.dry_run,
            )
            append_run_log(repo_root, {"action": "semantic_lock_check", "returncode": rc})
        elif choice == "6":
            rc = run_python(
                scripts_dir / BASE_SCRIPTS["orchestrate"],
                [
                    "--repo-root", str(repo_root),
                    "--raw-input-dir", args.raw_input_dir,
                    "--batch-label", args.batch_label,
                    "--feature-set-version", args.feature_set_version,
                    "--serve-html",
                    "--html-port", str(args.html_port),
                ],
                repo_root,
                args.dry_run,
            )
            append_run_log(repo_root, {"action": "serve_html", "returncode": rc})
        elif choice == "7":
            existing, missing = inspect_artifacts(repo_root)
            print("[info] existing critical artifacts:")
            for rel in existing:
                print(f"  [ok] {rel}")
            print("[info] missing critical artifacts:")
            for rel in missing:
                print(f"  [missing] {rel}")
            append_run_log(repo_root, {"action": "inspect_artifacts", "existing": existing, "missing": missing})
        elif choice == "8":
            stage = input("Resume from stage [bootstrap|ensure_demo_input|ingest|curate|features|train|evaluate|visualize]: ").strip()
            valid = ["bootstrap", "ensure_demo_input", "ingest", "curate", "features", "train", "evaluate", "visualize"]
            if stage not in valid:
                print("[error] invalid stage")
                continue
            rc = run_python(
                scripts_dir / BASE_SCRIPTS["orchestrate"],
                [
                    "--repo-root", str(repo_root),
                    "--source-id", args.source_id,
                    "--source-name", args.source_name,
                    "--source-kind", args.source_kind,
                    "--provider", args.provider,
                    "--raw-input-dir", args.raw_input_dir,
                    "--batch-label", args.batch_label,
                    "--ingest-mode", args.ingest_mode,
                    "--curation-version", args.curation_version,
                    "--feature-set-version", args.feature_set_version,
                    "--window-spec", args.window_spec,
                    "--resume-from", stage,
                    *(["--strict"] if args.strict else []),
                    *(["--dry-run"] if args.dry_run else []),
                ],
                repo_root,
                args.dry_run,
            )
            append_run_log(repo_root, {"action": "resume_from", "stage": stage, "returncode": rc})
        elif choice == "9":
            batch_id, feature_id = latest_ids(repo_root)
            status = latest_status(repo_root)
            print(f"[info] latest_ingest_batch_id={batch_id}")
            print(f"[info] latest_feature_generation_id={feature_id}")
            print(f"[info] latest_run_status={status}")
            append_run_log(repo_root, {"action": "show_latest_status", "status": status, "batch_id": batch_id, "feature_generation_id": feature_id})
        else:
            print("[error] invalid option")

if __name__ == "__main__":
    raise SystemExit(main())
