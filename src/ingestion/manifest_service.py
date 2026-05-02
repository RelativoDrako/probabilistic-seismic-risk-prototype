from __future__ import annotations

import mimetypes
import sqlite3
from pathlib import Path

from src.common.clock import utc_now_iso
from src.common.contracts import MANIFEST_VERSION, TABLE_RAW_ASSET_MANIFEST
from src.common.hashing import sha256_file
from src.common.ids import build_raw_asset_id
from src.ingestion.models import RawFileDescriptor


def scan_raw_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw input directory does not exist: {raw_dir}")
    if not raw_dir.is_dir():
        raise NotADirectoryError(f"Raw input path is not a directory: {raw_dir}")

    paths: list[Path] = []
    for path in raw_dir.rglob("*"):
        if not path.is_file():
            continue
        if "_meta" in path.parts:
            continue
        if path.suffix.lower() != ".csv":
            continue
        paths.append(path)

    return sorted(paths)


def build_raw_file_descriptor(
    *,
    source_id: str,
    ingest_batch_id: str,
    absolute_path: Path,
    raw_root_dir: Path,
    source_published_at_utc: str | None = None,
) -> RawFileDescriptor:
    absolute_path = absolute_path.resolve()
    raw_root_dir = raw_root_dir.resolve()

    try:
        relative_path = absolute_path.relative_to(raw_root_dir).as_posix()
    except ValueError as exc:
        raise ValueError(
            f"File {absolute_path} is outside declared raw root {raw_root_dir}"
        ) from exc

    content_type, _ = mimetypes.guess_type(str(absolute_path))

    return RawFileDescriptor(
        source_id=source_id,
        ingest_batch_id=ingest_batch_id,
        absolute_path=absolute_path,
        relative_path=relative_path,
        file_name=absolute_path.name,
        content_sha256=sha256_file(absolute_path),
        file_size_bytes=absolute_path.stat().st_size,
        content_type=content_type,
        downloaded_at_utc=utc_now_iso(),
        source_published_at_utc=source_published_at_utc,
    )


def register_raw_asset(conn: sqlite3.Connection, descriptor: RawFileDescriptor) -> str:
    raw_asset_id = build_raw_asset_id(
        source_id=descriptor.source_id,
        content_sha256=descriptor.content_sha256,
    )

    existing_by_hash = conn.execute(
        f"""
        SELECT raw_asset_id, relative_path, file_name, content_sha256
        FROM {TABLE_RAW_ASSET_MANIFEST}
        WHERE content_sha256 = ?
        """,
        (descriptor.content_sha256,),
    ).fetchone()

    if existing_by_hash is not None:
        if existing_by_hash["relative_path"] != descriptor.relative_path:
            raise ValueError(
                "Raw asset hash conflict: identical content already registered at a "
                f"different path ({existing_by_hash['relative_path']} != {descriptor.relative_path})."
            )
        return str(existing_by_hash["raw_asset_id"])

    existing_by_path = conn.execute(
        f"""
        SELECT raw_asset_id, relative_path, content_sha256
        FROM {TABLE_RAW_ASSET_MANIFEST}
        WHERE relative_path = ?
        """,
        (descriptor.relative_path,),
    ).fetchone()

    if existing_by_path is not None and existing_by_path["content_sha256"] != descriptor.content_sha256:
        raise ValueError(
            "Raw asset path conflict: same relative_path already exists with different content hash "
            f"({descriptor.relative_path})."
        )

    conn.execute(
        f"""
        INSERT INTO {TABLE_RAW_ASSET_MANIFEST} (
            raw_asset_id,
            ingest_batch_id,
            source_id,
            relative_path,
            file_name,
            content_sha256,
            file_size_bytes,
            content_type,
            source_published_at_utc,
            downloaded_at_utc,
            manifest_version,
            is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            raw_asset_id,
            descriptor.ingest_batch_id,
            descriptor.source_id,
            descriptor.relative_path,
            descriptor.file_name,
            descriptor.content_sha256,
            descriptor.file_size_bytes,
            descriptor.content_type,
            descriptor.source_published_at_utc,
            descriptor.downloaded_at_utc,
            MANIFEST_VERSION,
        ),
    )
    conn.commit()
    return raw_asset_id


def register_raw_assets(conn: sqlite3.Connection, descriptors: list[RawFileDescriptor]) -> list[str]:
    raw_asset_ids: list[str] = []
    for descriptor in descriptors:
        raw_asset_ids.append(register_raw_asset(conn, descriptor))
    return raw_asset_ids
