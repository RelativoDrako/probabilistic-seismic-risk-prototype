from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run ingest with persistent trace.")
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    logs = repo_root / "_ops_logs"
    logs.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "src.ingestion.cli",
        "--source-id", "ssn_demo",
        "--source-name", "SSN Demo",
        "--source-kind", "catalog",
        "--provider", "SSN",
        "--raw-input-dir", "data/raw/ssn_demo_input",
        "--batch-label", "demo_batch_001",
        "--ingest-mode", "manual",
    ]

    proc = subprocess.run(cmd, cwd=str(repo_root), text=True, capture_output=True)
    log_path = logs / "ingest_trace.log"
    log_path.write_text(
        "STDOUT:\n" + (proc.stdout or "") + "\n\nSTDERR:\n" + (proc.stderr or ""),
        encoding="utf-8",
    )

    payload = {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout_tail": (proc.stdout or "")[-4000:],
        "stderr_tail": (proc.stderr or "")[-4000:],
        "log_path": str(log_path),
    }
    json_path = logs / "ingest_trace.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] ingest_trace_json={json_path}")
    print(f"[ok] ingest_trace_log={log_path}")
    return proc.returncode

if __name__ == "__main__":
    raise SystemExit(main())
