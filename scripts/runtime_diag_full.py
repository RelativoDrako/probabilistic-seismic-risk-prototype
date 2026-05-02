from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

CHECK_MODULES = [
    "src.common.settings",
    "src.common.paths",
    "src.common.sqlite",
    "src.common.bootstrap_db",
    "src.common.contracts",
    "src.ingestion.cli",
    "src.ingestion.ingest_service",
    "src.processing.cli",
    "src.features.cli",
    "src.training.cli",
    "src.evaluation.cli",
    "src.visualization.cli",
]

CHECK_ATTRS = {
    "src.common.settings": ["load_settings", "get_settings"],
    "src.common.paths": ["get_sqlite_path", "canonical_db_path", "ensure_runtime_dirs"],
    "src.common.sqlite": ["connect_sqlite", "ensure_sqlite_parent_dir"],
    "src.common.contracts": [
        "TABLE_SOURCES",
        "TABLE_INGEST_BATCHES",
        "TABLE_RAW_ASSET_MANIFEST",
        "TABLE_CURATED_EVENTS",
        "TABLE_FEATURE_GENERATIONS",
        "TABLE_REGION_FEATURES",
        "TABLE_PIPELINE_RUN_JOURNAL",
    ],
}

def find_project_python(repo_root: Path) -> Path:
    if platform.system().lower().startswith("win"):
        candidate = repo_root / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = repo_root / ".venv" / "bin" / "python"
    return candidate if candidate.exists() else Path(sys.executable)

def import_check(py: Path, repo_root: Path, module_name: str) -> dict:
    proc = subprocess.run(
        [str(py), "-c", f"import {module_name}; print('ok')"],
        cwd=str(repo_root),
        text=True,
        capture_output=True,
    )
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout[-1000:],
        "stderr": proc.stderr[-2000:],
    }

def attr_check(py: Path, repo_root: Path, module_name: str, attrs: list[str]) -> dict:
    joined = ",".join([repr(a) for a in attrs])
    code = (
        f"import {module_name} as m; "
        f"import json; "
        f"print(json.dumps({{a: hasattr(m, a) for a in [{joined}]}}))"
    )
    proc = subprocess.run([str(py), "-c", code], cwd=str(repo_root), text=True, capture_output=True)
    payload = {}
    if proc.returncode == 0 and proc.stdout.strip():
        try:
            payload = json.loads(proc.stdout.strip())
        except Exception:
            payload = {"_parse_error": proc.stdout.strip()}
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout[-1000:],
        "stderr": proc.stderr[-2000:],
        "attributes": payload,
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a broader runtime compatibility report.")
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    py = find_project_python(repo_root)
    logs_dir = repo_root / "_ops_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "python": str(py),
        "python_version": platform.python_version(),
        "repo_root": str(repo_root),
        "modules": {},
        "attributes": {},
    }

    for module in CHECK_MODULES:
        report["modules"][module] = import_check(py, repo_root, module)

    for module, attrs in CHECK_ATTRS.items():
        report["attributes"][module] = attr_check(py, repo_root, module, attrs)

    out = logs_dir / "runtime_diag_full_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[ok] runtime_diag_full_report={out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
