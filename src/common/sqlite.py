from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .paths import canonical_db_path


def ensure_sqlite_parent_dir(db_path: str | Path | None = None) -> Path:
    path = Path(db_path).expanduser().resolve() if db_path is not None else canonical_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect_sqlite(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = ensure_sqlite_parent_dir(db_path)

    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")

    return connection


@contextmanager
def managed_connection(db_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    connection = connect_sqlite(db_path)
    try:
        yield connection
    finally:
        connection.close()


@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise


__all__ = [
    "ensure_sqlite_parent_dir",
    "connect_sqlite",
    "managed_connection",
    "transaction",
]
