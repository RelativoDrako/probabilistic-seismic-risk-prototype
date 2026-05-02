from __future__ import annotations

import argparse
import json
import platform
import sqlite3
import subprocess
import sys
from pathlib import Path

CHECK_MODULES = [
    "src.common.settings",
    "src.common.paths",
    "src.common.sqlite",
    "src.common.bootstrap_db",
    "src.ingestion.cli",
    "src.processing.cli",
    "src.features.cli",
    "src.training.cli",
    "src.evaluation.cli",
    "src.visualization.cli",
]

CHECK_FUNCTIONS = {
    "src.common.settings": ["load_settings", "get_settings"],
    "src.common.paths": ["get_sqlite_path", "canonical_db_path", "ensure_runtime_dirs"],
}


def find_project_python(repo_root: Path) -> Path:
    if platform.system().lower().startswith("win"):
        candidate = repo_root / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = repo_root / ".venv" / "bin" / "python"
    return candidate if candidate.exists() else Path(sys.executable)


def run_import_check(py: Path, repo_root: Path, module_name: str) -> dict:
    code = f"import {module_name}; print('ok')"
    proc = subprocess.run([str(py), "-c", code], cwd=str(repo_root), text=True, capture_output=True)
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout[-1000:],
        "stderr": proc.stderr[-2000:],
    }


def run_attr_check(py: Path, repo_root: Path, module_name: str, attrs: list[str]) -> dict:
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


def latest_ids(db_path: Path) -> tuple[str | None, str | None]:
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a temporary runtime diagnostic report.")
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
        report["modules"][module] = run_import_check(py, repo_root, module)

    for module, attrs in CHECK_FUNCTIONS.items():
        report["attributes"][module] = run_attr_check(py, repo_root, module, attrs)

    db_path = repo_root / "artifacts" / "sqlite" / "seismic_prototype.db"
    batch_id, feature_id = latest_ids(db_path)
    report["latest_ingest_batch_id"] = batch_id
    report["latest_feature_generation_id"] = feature_id

    out = logs_dir / "runtime_diag_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[ok] runtime_diag_report={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
