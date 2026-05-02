from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LocalSettings:
    repo_root: Path
    data_dir: Path
    raw_dir: Path
    artifacts_dir: Path
    sqlite_dir: Path
    sqlite_path: Path

    @property
    def db_path(self) -> Path:
        """Compatibility alias for legacy callers that still expect db_path."""
        return self.sqlite_path


def _detect_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_settings(repo_root: str | Path | None = None) -> LocalSettings:
    root = Path(repo_root).resolve() if repo_root is not None else _detect_repo_root()
    artifacts_dir = root / "artifacts"
    sqlite_dir = artifacts_dir / "sqlite"
    return LocalSettings(
        repo_root=root,
        data_dir=root / "data",
        raw_dir=root / "data" / "raw",
        artifacts_dir=artifacts_dir,
        sqlite_dir=sqlite_dir,
        sqlite_path=sqlite_dir / "seismic_prototype.db",
    )


def get_settings(repo_root: str | Path | None = None) -> LocalSettings:
    return load_settings(repo_root)
