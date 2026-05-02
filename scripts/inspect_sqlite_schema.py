from __future__ import annotations
import argparse, json, sqlite3
from pathlib import Path

def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--table", required=True)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    db_path = repo_root / "artifacts" / "sqlite" / "seismic_prototype.db"
    out_path = repo_root / "_ops_logs" / f"schema_inspect_{args.table}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        table_info = conn.execute(f"PRAGMA table_info({args.table})").fetchall()
        index_list = conn.execute(f"PRAGMA index_list({args.table})").fetchall()
        index_info = {}
        for idx in index_list:
            idx_name = idx[1]
            index_info[idx_name] = conn.execute(f"PRAGMA index_info({idx_name})").fetchall()
    finally:
        conn.close()

    payload = {
        "table": args.table,
        "table_info": [list(x) for x in table_info],
        "index_list": [list(x) for x in index_list],
        "index_info": {k: [list(x) for x in v] for k, v in index_info.items()},
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] report={out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
