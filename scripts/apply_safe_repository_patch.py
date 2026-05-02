from __future__ import annotations
import argparse, json, shutil
from pathlib import Path

NEW_FUNCTION = '''def insert_region_features(conn, rows):
    sql = """
    INSERT INTO region_features (
        feature_row_id,
        feature_generation_id,
        feature_set_version,
        region_code,
        window_start_utc,
        window_end_utc,
        event_count,
        max_magnitude,
        mean_magnitude,
        mean_depth_km,
        days_since_last_event,
        target_label,
        created_at_utc
    )
    VALUES (
        :feature_row_id,
        :feature_generation_id,
        :feature_set_version,
        :region_code,
        :window_start_utc,
        :window_end_utc,
        :event_count,
        :max_magnitude,
        :mean_magnitude,
        :mean_depth_km,
        :days_since_last_event,
        :target_label,
        :created_at_utc
    )
    ON CONFLICT(
        feature_generation_id,
        region_code,
        window_start_utc,
        window_end_utc
    )
    DO UPDATE SET
        event_count = excluded.event_count,
        max_magnitude = excluded.max_magnitude,
        mean_magnitude = excluded.mean_magnitude,
        mean_depth_km = excluded.mean_depth_km,
        days_since_last_event = excluded.days_since_last_event,
        target_label = excluded.target_label
    """
    cur = conn.cursor()
    for r in rows:
        cur.execute(sql, r)
    conn.commit()
    return len(rows)
'''.strip('\n')

def replace_function(text: str) -> str:
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith('def insert_region_features'):
            start = i
            break
    if start is None:
        raise RuntimeError('insert_region_features not found')
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith('def ') and not lines[j].startswith('def insert_region_features'):
            end = j
            break
    return '\n'.join(lines[:start] + NEW_FUNCTION.splitlines() + lines[end:]) + '\n'

def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', required=True)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    repo_file = repo_root / 'src' / 'features' / 'repository.py'
    backup = repo_root / 'src' / 'features' / 'repository.pre_guardrails_fix.bak'
    out_path = repo_root / '_ops_logs' / 'apply_safe_repository_patch_report.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(repo_file, backup)
    original = repo_file.read_text(encoding='utf-8')
    repo_file.write_text(replace_function(original), encoding='utf-8')
    out_path.write_text(json.dumps({
        'repository_path': str(repo_file),
        'backup_path': str(backup),
        'status': 'patched',
    }, indent=2), encoding='utf-8')
    print(f'[ok] backup={backup}')
    print(f'[ok] repository_patched={repo_file}')
    print(f'[ok] report={out_path}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
