from __future__ import annotations
import argparse, json, sqlite3
from pathlib import Path

TARGET_UNIQUE = ["feature_generation_id", "region_code", "window_start_utc", "window_end_utc"]

def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    db_path = repo_root / "artifacts" / "sqlite" / "seismic_prototype.db"
    out_sql = repo_root / "_ops_logs" / "generated_region_features_migration.sql"
    out_json = repo_root / "_ops_logs" / "generated_region_features_migration_report.json"
    out_sql.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        cols = conn.execute("PRAGMA table_info(region_features)").fetchall()
    finally:
        conn.close()

    schema_cols = [{"name": c[1], "type": c[2], "notnull": c[3], "pk": c[5]} for c in cols]
    col_names = [c["name"] for c in schema_cols]
    missing_unique_cols = [c for c in TARGET_UNIQUE if c not in col_names]

    create_cols, insert_cols, select_cols = [], [], []
    for c in schema_cols:
        col_def = f'{c["name"]} {c["type"] or "TEXT"}'
        if c["pk"]:
            col_def += " PRIMARY KEY"
        elif c["notnull"]:
            col_def += " NOT NULL"
        create_cols.append(col_def)
        insert_cols.append(c["name"])
        select_cols.append(c["name"])

    if not missing_unique_cols:
        create_cols.append("UNIQUE (feature_generation_id, region_code, window_start_utc, window_end_utc)")

    sql = []
    sql.append("PRAGMA foreign_keys=OFF;")
    sql.append("BEGIN TRANSACTION;")
    sql.append("CREATE TABLE IF NOT EXISTS region_features_new (")
    sql.append("    " + ",\n    ".join(create_cols))
    sql.append(");")
    sql.append("")
    sql.append("INSERT INTO region_features_new (")
    sql.append("    " + ",\n    ".join(insert_cols))
    sql.append(")")
    sql.append("SELECT")
    sql.append("    " + ",\n    ".join(select_cols))
    sql.append("FROM region_features;")
    sql.append("")
    sql.append("DROP TABLE region_features;")
    sql.append("ALTER TABLE region_features_new RENAME TO region_features;")
    sql.append("COMMIT;")
    sql.append("PRAGMA foreign_keys=ON;")

    out_sql.write_text("\n".join(sql) + "\n", encoding="utf-8")
    out_json.write_text(json.dumps({
        "schema_columns": col_names,
        "missing_unique_columns": missing_unique_cols,
        "generated_sql": str(out_sql),
        "safe_to_use_directly": not missing_unique_cols,
    }, indent=2), encoding="utf-8")
    print(f"[ok] sql={out_sql}")
    print(f"[ok] report={out_json}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
