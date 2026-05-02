from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path


def venv_python(venv_dir: Path) -> Path:
    if platform.system().lower().startswith("win"):
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create and configure local virtual environment.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--venv-dir", default=".venv")
    parser.add_argument("--requirements", default="requirements-demo.txt")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    venv_dir = repo_root / args.venv_dir
    requirements = repo_root / args.requirements

    if not requirements.exists():
        print(f"[error] requirements file not found: {requirements}")
        return 2

    if args.dry_run:
        print(f"[dry-run] venv={venv_dir}")
        print(f"[dry-run] requirements={requirements}")
        return 0

    if not venv_dir.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    py = venv_python(venv_dir)
    if not py.exists():
        print(f"[error] venv python not found: {py}")
        return 3

    subprocess.run([str(py), "-m", "pip", "install", "--upgrade", "pip", "wheel", "setuptools"], check=True)
    subprocess.run([str(py), "-m", "pip", "install", "-r", str(requirements)], check=True)

    print(f"[ok] venv_python={py}")
    print("[ok] environment configured")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
