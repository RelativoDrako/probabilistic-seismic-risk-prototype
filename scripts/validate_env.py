from __future__ import annotations

import argparse
import json
import platform
import sqlite3
import subprocess
import sys
from pathlib import Path

REQUIRED_IMPORTS = ["matplotlib", "pandas", "sklearn", "joblib"]
REQUIRED_ENTRYPOINTS = [
    "src.common.bootstrap_db",
    "src.ingestion.cli",
    "src.processing.cli",
    "src.features.cli",
    "src.training.cli",
    "src.evaluation.cli",
    "src.visualization.cli",
]
EXPECTED_PATHS = [
    "data",
    "artifacts",
    "scripts",
    "src",
]

def find_project_python(repo_root: Path) -> Path:
    if platform.system().lower().startswith("win"):
        candidate = repo_root / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = repo_root / ".venv" / "bin" / "python"
    return candidate if candidate.exists() else Path(sys.executable)

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

def module_check(py: Path, repo_root: Path, module_name: str) -> dict:
    cmd = [str(py), "-c", f"import {module_name}; print('ok')"]
    proc = subprocess.run(cmd, cwd=str(repo_root), text=True, capture_output=True)
    if proc.returncode == 0 and "ok" in proc.stdout:
        return {"status": "ok", "detail": ""}
    stderr = (proc.stderr or proc.stdout).strip()
    return {"status": "error", "detail": stderr[-500:]}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate environment and repo structure.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    py = find_project_python(repo_root)

    results = {
        "python": str(py),
        "python_version": platform.python_version(),
        "imports": {},
        "entrypoints": {},
        "paths": {},
    }

    for module in REQUIRED_IMPORTS:
        results["imports"][module] = module_check(py, repo_root, module)

    for entry in REQUIRED_ENTRYPOINTS:
        results["entrypoints"][entry] = module_check(py, repo_root, entry)

    for rel in EXPECTED_PATHS:
        results["paths"][rel] = {"status": "ok" if (repo_root / rel).exists() else "error"}

    db_path = repo_root / "artifacts" / "sqlite" / "seismic_prototype.db"
    batch_id, feature_generation_id = latest_ids(db_path)
    results["latest_ingest_batch_id"] = batch_id
    results["latest_feature_generation_id"] = feature_generation_id

    logs_dir = repo_root / "_ops_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    report = logs_dir / "validate_env_report.json"
    report.write_text(json.dumps(results, indent=2), encoding="utf-8")

    failures = []
    failures.extend(k for k, v in results["imports"].items() if v["status"] != "ok")
    failures.extend(k for k, v in results["entrypoints"].items() if v["status"] != "ok")
    failures.extend(k for k, v in results["paths"].items() if v["status"] != "ok")

    print(f"[ok] report={report}")
    print(f"[info] latest_ingest_batch_id={batch_id}")
    print(f"[info] latest_feature_generation_id={feature_generation_id}")

    if failures:
        print(f"[warn] validation_failures={','.join(failures)}")
        for failed in failures:
            if failed in results["entrypoints"]:
                detail = results["entrypoints"][failed]["detail"]
                if detail:
                    print(f"[detail] {failed}: {detail}")
            if failed in results["imports"]:
                detail = results["imports"][failed]["detail"]
                if detail:
                    print(f"[detail] {failed}: {detail}")
        return 1 if args.strict else 0

    print("[ok] environment validation passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
