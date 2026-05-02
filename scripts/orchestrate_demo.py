from __future__ import annotations

import argparse
import http.server
import json
import platform
import socketserver
import sqlite3
import subprocess
import sys
import threading
from pathlib import Path

STAGES = ["bootstrap", "ensure_demo_input", "ingest", "curate", "features", "train", "evaluate", "visualize"]

def project_python(repo_root: Path) -> Path:
    if platform.system().lower().startswith("win"):
        candidate = repo_root / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = repo_root / ".venv" / "bin" / "python"
    return candidate if candidate.exists() else Path(sys.executable)

def run_step(cmd: list[str], cwd: Path, stage: str, log_lines: list[dict], dry_run: bool = False) -> None:
    if dry_run:
        log_lines.append({"stage": stage, "cmd": cmd, "returncode": 0, "stdout": "[dry-run]", "stderr": ""})
        print(f"[dry-run] {' '.join(cmd)}")
        return

    proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)
    log_lines.append({
        "stage": stage,
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-6000:],
        "stderr": proc.stderr[-6000:],
    })
    if proc.stdout:
        print(proc.stdout[-1000:])
    if proc.stderr:
        print(proc.stderr[-1000:])
    print(f"[step] {stage} -> rc={proc.returncode}")

    # Visualización: tolerar warnings si se generaron artefactos
    if stage == "visualize":
        if proc.returncode != 0:
            stderr_lower = (proc.stderr or "").lower()
            artifacts_dir = cwd / "artifacts" / "reports"
            evidence_md = artifacts_dir / "demo_evidence.md"
            evidence_json = artifacts_dir / "demo_evidence.json"
            if "userwarning" in stderr_lower and (evidence_md.exists() or evidence_json.exists()):
                print("[warn] visualize returned non-zero but evidence artifacts exist; continuing")
                return

    if proc.returncode != 0:
        raise RuntimeError(f"stage failed: {stage}")

def latest_ingest_batch_id(db_path: Path, source_id: str, batch_label: str | None = None) -> str | None:
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        if batch_label:
            row = conn.execute(
                """
                SELECT ingest_batch_id
                FROM ingest_batches
                WHERE source_id = ? AND batch_label = ?
                ORDER BY started_at_utc DESC
                LIMIT 1
                """,
                (source_id, batch_label),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT ingest_batch_id
                FROM ingest_batches
                WHERE source_id = ?
                ORDER BY started_at_utc DESC
                LIMIT 1
                """,
                (source_id,),
            ).fetchone()
        return None if row is None else row["ingest_batch_id"]
    finally:
        conn.close()

def serve_html(directory: Path, port: int):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

    httpd = socketserver.TCPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return thread, httpd

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Controlled orchestration for the seismic demo pipeline.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--source-id", default="usgs_demo")
    parser.add_argument("--source-name", default="USGS Demo")
    parser.add_argument("--source-kind", default="catalog")
    parser.add_argument("--provider", default="USGS")
    parser.add_argument("--raw-input-dir", default="data/raw/ssn_demo_input")
    parser.add_argument("--batch-label", default="demo_batch_usgs_001")
    parser.add_argument("--ingest-mode", default="manual")
    parser.add_argument("--curation-version", default="v1")
    parser.add_argument("--feature-set-version", default="v1")
    parser.add_argument("--window-spec", default="30d")
    parser.add_argument("--serve-html", action="store_true")
    parser.add_argument("--html-port", type=int, default=8008)
    parser.add_argument("--resume-from", choices=STAGES, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    py = project_python(repo_root)
    db_path = repo_root / "artifacts" / "sqlite" / "seismic_prototype.db"
    logs_dir = repo_root / "_ops_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_lines: list[dict] = []

    start_index = 0 if args.resume_from is None else STAGES.index(args.resume_from)

    try:
        print(f"[info] source_id={args.source_id}")
        print(f"[info] raw_input_dir={args.raw_input_dir}")
        print(f"[info] batch_label={args.batch_label}")
        print(f"[info] resume_from={args.resume_from or 'bootstrap'}")

        if start_index <= STAGES.index("bootstrap"):
            run_step([str(py), "-m", "src.common.bootstrap_db"], repo_root, "bootstrap", log_lines, args.dry_run)

        if start_index <= STAGES.index("ensure_demo_input"):
            ensure_script = repo_root / "scripts" / "ensure_demo_input.py"
            if ensure_script.exists():
                run_step([str(py), str(ensure_script), "--repo-root", str(repo_root), "--raw-input-dir", args.raw_input_dir], repo_root, "ensure_demo_input", log_lines, args.dry_run)
            else:
                print("[info] ensure_demo_input.py not present; skipping ensure_demo_input stage")

        raw_input_dir = repo_root / args.raw_input_dir
        if not args.dry_run and raw_input_dir.exists():
            raw_files = [p for p in raw_input_dir.rglob("*") if p.is_file()]
            print(f"[info] raw_files_detected={len(raw_files)}")
            if not raw_files and start_index <= STAGES.index("ingest"):
                print(f"[error] no raw files found before ingestion: {raw_input_dir}")
                return 2

        if start_index <= STAGES.index("ingest"):
            run_step(
                [
                    str(py), "-m", "src.ingestion.cli",
                    "--source-id", args.source_id,
                    "--source-name", args.source_name,
                    "--source-kind", args.source_kind,
                    "--provider", args.provider,
                    "--raw-input-dir", args.raw_input_dir,
                    "--batch-label", args.batch_label,
                    "--ingest-mode", args.ingest_mode,
                ],
                repo_root, "ingest", log_lines, args.dry_run
            )

        ingest_batch_id = "DRY_RUN_BATCH" if args.dry_run else latest_ingest_batch_id(db_path, args.source_id, args.batch_label)
        if not ingest_batch_id:
            print("[error] unable to resolve ingest_batch_id after ingestion")
            return 3

        print(f"[info] resolved_ingest_batch_id={ingest_batch_id}")

        downstream = [
            ("curate", [str(py), "-m", "src.processing.cli", "--source-id", args.source_id, "--ingest-batch-id", ingest_batch_id, "--curation-version", args.curation_version]),
            ("features", [str(py), "-m", "src.features.cli", "--ingest-batch-id", ingest_batch_id, "--feature-set-version", args.feature_set_version, "--window-spec", args.window_spec]),
            ("train", [str(py), "-m", "src.training.cli", "--ingest-batch-id", ingest_batch_id, "--feature-set-version", args.feature_set_version]),
            ("evaluate", [str(py), "-m", "src.evaluation.cli", "--ingest-batch-id", ingest_batch_id, "--feature-set-version", args.feature_set_version]),
            ("visualize", [str(py), "-m", "src.visualization.cli", "--ingest-batch-id", ingest_batch_id, "--feature-set-version", args.feature_set_version]),
        ]

        for stage, cmd in downstream:
            if start_index <= STAGES.index(stage):
                run_step(cmd, repo_root, stage, log_lines, args.dry_run)

        html_url = None
        if args.serve_html and not args.dry_run:
            html_dir = repo_root / "presentations" / "final"
            html_file = html_dir / "earthquake_evaluation_final.html"
            if html_file.exists():
                _, httpd = serve_html(html_dir, args.html_port)
                html_url = f"http://127.0.0.1:{args.html_port}/earthquake_evaluation_final.html"
                print(f"[ok] html_url={html_url}")
                print("[info] open the URL in the browser and validate the operational flow visually")
                httpd.shutdown()
                httpd.server_close()
            else:
                print("[warn] final HTML presentation not found; skipping serve_html")

        critical = [
            repo_root / "artifacts" / "reports" / "metrics.json",
            repo_root / "artifacts" / "reports" / "evaluation_summary.md",
            repo_root / "artifacts" / "reports" / "demo_evidence.md",
        ]
        missing = [str(p.relative_to(repo_root)) for p in critical if not args.dry_run and not p.exists()]
        report = {
            "run_status": "PASS" if not missing else "FAIL",
            "ingest_batch_id": ingest_batch_id,
            "feature_set_version": args.feature_set_version,
            "html_validation_url": html_url,
            "missing_artifacts": missing,
            "steps": log_lines,
        }
        report_path = logs_dir / "orchestrate_demo_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        print(f"PREDEMO_STATUS={report['run_status']}")
        print(f"[ok] ingest_batch_id={ingest_batch_id}")
        print(f"[ok] report={report_path}")

        if missing and args.strict:
            return 4
        return 0 if not missing else 1

    except Exception as exc:
        report = {
            "run_status": "FAIL",
            "error": str(exc),
            "steps": log_lines,
        }
        report_path = logs_dir / "orchestrate_demo_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"[error] {exc}")
        print(f"[ok] report={report_path}")
        return 5

if __name__ == "__main__":
    raise SystemExit(main())
