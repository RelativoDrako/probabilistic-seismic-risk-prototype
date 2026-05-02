from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

CHECKS = {
    "src.common.ids": ["build_ingest_batch_id", "build_event_id", "build_raw_asset_id", "build_pipeline_run_id"],
    "src.common.bootstrap_db": [],
    "src.ingestion.batch_registry": [],
    "src.ingestion.source_registry": [],
    "src.ingestion.manifest_service": [],
    "src.ingestion.ingest_service": [],
    "src.ingestion.cli": [],
}

def find_project_python(repo_root: Path) -> Path:
    if platform.system().lower().startswith("win"):
        candidate = repo_root / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = repo_root / ".venv" / "bin" / "python"
    return candidate if candidate.exists() else Path(sys.executable)

def import_check(py: Path, repo_root: Path, module_name: str) -> dict:
    proc = subprocess.run([str(py), "-c", f"import {module_name}; print('ok')"], cwd=str(repo_root), text=True, capture_output=True)
    return {"returncode": proc.returncode, "stdout": proc.stdout[-1000:], "stderr": proc.stderr[-2000:]}

def attr_check(py: Path, repo_root: Path, module_name: str, attrs: list[str]) -> dict:
    if not attrs:
        return {"returncode": 0, "attributes": {}}
    joined = ",".join([repr(a) for a in attrs])
    code = f"import {module_name} as m; import json; print(json.dumps({{a: hasattr(m, a) for a in [{joined}]}}))"
    proc = subprocess.run([str(py), "-c", code], cwd=str(repo_root), text=True, capture_output=True)
    payload = {}
    if proc.returncode == 0 and proc.stdout.strip():
        try:
            payload = json.loads(proc.stdout.strip())
        except Exception:
            payload = {"_parse_error": proc.stdout.strip()}
    return {"returncode": proc.returncode, "stdout": proc.stdout[-1000:], "stderr": proc.stderr[-2000:], "attributes": payload}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Runtime contracts guard.")
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    py = find_project_python(repo_root)
    logs_dir = repo_root / "_ops_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    report = {"python": str(py), "python_version": platform.python_version(), "repo_root": str(repo_root), "modules": {}, "attributes": {}}

    for module, attrs in CHECKS.items():
        report["modules"][module] = import_check(py, repo_root, module)
        report["attributes"][module] = attr_check(py, repo_root, module, attrs)

    out = logs_dir / "runtime_contracts_guard_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[ok] runtime_contracts_guard_report={out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
