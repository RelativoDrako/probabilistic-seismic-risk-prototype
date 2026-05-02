from __future__ import annotations
import argparse, json
from pathlib import Path

STAGE_FILES = {
    "features": [
        "src/features/cli.py",
        "src/features/feature_service.py",
        "src/features/repository.py",
        "src/features/builders.py",
        "src/features/models.py",
    ]
}

def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--stage", required=True, choices=sorted(STAGE_FILES))
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    out_path = repo_root / "_ops_logs" / f"stage_contract_{args.stage}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {"stage": args.stage, "files": {}}
    for rel in STAGE_FILES[args.stage]:
        p = repo_root / rel
        payload["files"][rel] = p.read_text(encoding="utf-8").splitlines()[:200] if p.exists() else None

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[ok] report={out_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
