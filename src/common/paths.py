from __future__ import annotations

from pathlib import Path
from .settings import get_settings


def get_repo_root() -> Path:
    return get_settings().repo_root


def get_data_dir() -> Path:
    return get_settings().data_dir


def get_raw_dir() -> Path:
    return get_settings().raw_dir


def get_artifacts_dir() -> Path:
    return get_settings().artifacts_dir


def get_sqlite_dir() -> Path:
    return get_settings().sqlite_dir


def get_sqlite_path() -> Path:
    return get_settings().sqlite_path


# Compatibility layer expected by src.common.sqlite
def canonical_db_path() -> Path:
    return get_sqlite_path()


def ensure_runtime_dirs() -> dict[str, Path]:
    settings = get_settings()
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    settings.sqlite_dir.mkdir(parents=True, exist_ok=True)
    settings.raw_dir.mkdir(parents=True, exist_ok=True)
    return {
        "repo_root": settings.repo_root,
        "data_dir": settings.data_dir,
        "raw_dir": settings.raw_dir,
        "artifacts_dir": settings.artifacts_dir,
        "sqlite_dir": settings.sqlite_dir,
        "sqlite_path": settings.sqlite_path,
    }
