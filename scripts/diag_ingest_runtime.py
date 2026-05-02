from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import inspect
import json
import traceback
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Diagnose ingest runtime and reader contract.")
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    logs = repo_root / "_ops_logs"
    logs.mkdir(parents=True, exist_ok=True)

    report = {
        "repo_root": str(repo_root),
        "reader_path": "",
        "reader_exists": False,
        "reader_sha256": "",
        "reader_preview": [],
        "csv_files": [],
        "csv_headers": {},
        "imports": {},
        "signatures": {},
        "sample_read_records_raw_input_dir": None,
        "sample_read_records_raw_file": None,
    }

    reader_path = repo_root / "src" / "ingestion" / "readers" / "ssn_reader.py"
    report["reader_path"] = str(reader_path)
    report["reader_exists"] = reader_path.exists()

    if reader_path.exists():
        content = reader_path.read_text(encoding="utf-8")
        report["reader_sha256"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
        report["reader_preview"] = content.splitlines()[:80]

    raw_dir = repo_root / "data" / "raw" / "ssn_demo_input"
    if raw_dir.exists():
        csv_files = sorted(raw_dir.glob("*.csv"))
        report["csv_files"] = [str(p) for p in csv_files]
        for csv_path in csv_files:
            with csv_path.open("r", encoding="utf-8-sig", newline="") as h:
                reader = csv.DictReader(h)
                report["csv_headers"][csv_path.name] = reader.fieldnames

    modules = [
        "src.ingestion.readers.ssn_reader",
        "src.ingestion.ingest_service",
        "src.ingestion.cli",
    ]

    for mod_name in modules:
        try:
            mod = importlib.import_module(mod_name)
            report["imports"][mod_name] = "ok"
            if hasattr(mod, "read_records"):
                report["signatures"][f"{mod_name}.read_records"] = str(inspect.signature(mod.read_records))
        except Exception:
            report["imports"][mod_name] = traceback.format_exc()

    try:
        reader_mod = importlib.import_module("src.ingestion.readers.ssn_reader")
        rr = getattr(reader_mod, "read_records")
        try:
            rows = []
            for idx, row in enumerate(rr(raw_input_dir=raw_dir)):
                rows.append(row)
                if idx >= 1:
                    break
            report["sample_read_records_raw_input_dir"] = {"ok": True, "rows": rows}
        except Exception:
            report["sample_read_records_raw_input_dir"] = {"ok": False, "error": traceback.format_exc()}

        if report["csv_files"]:
            first = Path(report["csv_files"][0])
            try:
                rows = []
                for idx, row in enumerate(rr(raw_file=first)):
                    rows.append(row)
                    if idx >= 1:
                        break
                report["sample_read_records_raw_file"] = {"ok": True, "rows": rows}
            except Exception:
                report["sample_read_records_raw_file"] = {"ok": False, "error": traceback.format_exc()}
    except Exception:
        pass

    out = logs / "diag_ingest_runtime.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[ok] diag_ingest_runtime={out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
