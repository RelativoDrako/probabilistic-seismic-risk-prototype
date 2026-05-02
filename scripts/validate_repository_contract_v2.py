from __future__ import annotations
import argparse
import json
import re
import sqlite3
from pathlib import Path

def extract_insert_region_features_block(text: str) -> str:
    marker = "def insert_region_features"
    start = text.find(marker)
    if start == -1:
        raise RuntimeError("insert_region_features not found")
    tail = text[start:]
    next_def = tail.find("\ndef ", len(marker))
    if next_def == -1:
        return tail
    return tail[:next_def]

def parse_insert_columns(block: str) -> list[str]:
    m = re.search(r"INSERT\s+INTO\s+region_features\s*\((.*?)\)\s*VALUES", block, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return []
    return [c.strip().strip('"').strip("'") for c in m.group(1).split(",") if c.strip()]

def parse_on_conflict_columns(block: str) -> list[str]:
    m = re.search(r"ON\s+CONFLICT\s*\((.*?)\)\s*DO\s+UPDATE", block, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return []
    return [c.strip().strip('"').strip("'") for c in m.group(1).split(",") if c.strip()]

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate region_features repository contract against SQLite schema.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--table", required=True)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    db_path = repo_root / "artifacts" / "sqlite" / "seismic_prototype.db"
    repo_file = repo_root / args.repository
    out_path = repo_root / "_ops_logs" / f"repository_contract_{args.table}_v2.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    text = repo_file.read_text(encoding="utf-8")
    block = extract_insert_region_features_block(text)
    insert_cols = parse_insert_columns(block)
    on_conflict_cols = parse_on_conflict_columns(block)

    conn = sqlite3.connect(str(db_path))
    try:
        table_info = conn.execute(f"PRAGMA table_info({args.table})").fetchall()
        schema_cols = [row[1] for row in table_info]
        idx_rows = conn.execute(f"PRAGMA index_list({args.table})").fetchall()
        unique_indexes = []
        for idx in idx_rows:
            idx_name = idx[1]
            is_unique = idx[2]
            cols = [r[2] for r in conn.execute(f"PRAGMA index_info({idx_name})").fetchall()]
            if is_unique:
                unique_indexes.append({"name": idx_name, "columns": cols})
    finally:
        conn.close()

    payload = {
        "table": args.table,
        "repository": str(repo_file),
        "schema_columns": schema_cols,
        "insert_columns": insert_cols,
        "on_conflict_columns": on_conflict_cols,
        "unique_indexes": unique_indexes,
        "missing_insert_columns": [c for c in insert_cols if c not in schema_cols],
        "conflict_supported": any(ui["columns"] == on_conflict_cols for ui in unique_indexes),
        "validated_block": "insert_region_features",
    }

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] report={out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
