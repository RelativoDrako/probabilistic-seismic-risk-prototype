from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path
from typing import Iterable

DEFAULT_ZIPS = [
    "seismic-early-detection-stage1-bootstrap.zip",
    "seismic_phase2_delivery.zip",
    "seismic_phase03_04_delivery.zip",
    "seismic_phase05_delivery.zip",
]


def extract_zip(zip_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(destination)


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file():
            yield path


def overlay_tree(source: Path, repo_root: Path, backup_root: Path, manifest: list[dict], dry_run: bool = False) -> None:
    for src in iter_files(source):
        rel = src.relative_to(source)
        dst = repo_root / rel
        entry = {"relative_path": str(rel), "action": "created"}
        if dst.exists():
            backup_target = backup_root / rel
            entry["action"] = "replaced"
            entry["backup"] = str(backup_target.relative_to(repo_root))
            if not dry_run:
                backup_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, backup_target)
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        manifest.append(entry)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply staged deliverable zips into the repo.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--zips", nargs="*", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    workspace_root = Path(args.workspace_root).resolve()
    zip_names = args.zips if args.zips else DEFAULT_ZIPS

    if not repo_root.exists():
        print(f"[error] repo root does not exist: {repo_root}")
        return 2
    if not workspace_root.exists():
        print(f"[error] workspace root does not exist: {workspace_root}")
        return 2

    staging_root = repo_root / "_ops_staging"
    backup_root = repo_root / "_ops_backup"
    logs_dir = repo_root / "_ops_logs"

    if not args.dry_run:
        for directory in (staging_root, backup_root, logs_dir):
            directory.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    missing: list[str] = []

    for zip_name in zip_names:
        zip_path = workspace_root / zip_name
        if not zip_path.exists():
            missing.append(zip_name)
            continue

        extract_dir = staging_root / zip_path.stem
        if not args.dry_run:
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir(parents=True, exist_ok=True)
            extract_zip(zip_path, extract_dir)
        else:
            extract_dir = workspace_root / f"__dryrun__{zip_path.stem}"
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir(parents=True, exist_ok=True)
            extract_zip(zip_path, extract_dir)

        overlay_tree(extract_dir, repo_root, backup_root, manifest, dry_run=args.dry_run)

    summary = {
        "repo_root": str(repo_root),
        "workspace_root": str(workspace_root),
        "applied_files": len(manifest),
        "missing_zips": missing,
        "dry_run": args.dry_run,
    }

    if not args.dry_run:
        manifest_path = logs_dir / "apply_deliverables_manifest.json"
        manifest_path.write_text(json.dumps({"summary": summary, "files": manifest}, indent=2), encoding="utf-8")
        print(f"[ok] manifest={manifest_path}")

    print(f"[ok] applied_files={len(manifest)}")
    if missing:
        print(f"[warn] missing_zips={','.join(missing)}")
        if args.strict:
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
