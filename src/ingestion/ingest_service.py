from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from src.common.contracts import TABLE_PIPELINE_RUN_JOURNAL
from src.common.ids import _build_prefixed_id  # uses the same deterministic primitive as Stage 1
from src.common.clock import utc_now_iso
from src.ingestion.batch_registry import complete_ingest_batch, fail_ingest_batch, start_ingest_batch
from src.ingestion.manifest_service import (
    build_raw_file_descriptor,
    register_raw_assets,
    scan_raw_files,
)
from src.ingestion.models import SourceDefinition
from src.ingestion.readers.ssn_reader import read_records
from src.ingestion.source_registry import register_source


@dataclass(frozen=True)
class IngestExecutionSummary:
    ingest_batch_id: str
    file_count: int
    record_count: int
    raw_asset_ids: tuple[str, ...]


def _build_pipeline_run_id(stage_name: str, stage_run_key: str) -> str:
    return _build_prefixed_id("pr", stage_name, stage_run_key)


def _upsert_pipeline_run(
    conn: sqlite3.Connection,
    *,
    stage_name: str,
    stage_run_key: str,
    related_entity_id: str | None,
    status: str,
    message: str | None,
    completed: bool,
) -> None:
    pipeline_run_id = _build_pipeline_run_id(stage_name, stage_run_key)
    existing = conn.execute(
        f"""
        SELECT pipeline_run_id
        FROM {TABLE_PIPELINE_RUN_JOURNAL}
        WHERE stage_name = ? AND stage_run_key = ?
        """,
        (stage_name, stage_run_key),
    ).fetchone()

    if existing is None:
        conn.execute(
            f"""
            INSERT INTO {TABLE_PIPELINE_RUN_JOURNAL} (
                pipeline_run_id,
                stage_name,
                stage_run_key,
                related_entity_id,
                status,
                started_at_utc,
                completed_at_utc,
                message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pipeline_run_id,
                stage_name,
                stage_run_key,
                related_entity_id,
                status,
                utc_now_iso(),
                utc_now_iso() if completed else None,
                message,
            ),
        )
    else:
        conn.execute(
            f"""
            UPDATE {TABLE_PIPELINE_RUN_JOURNAL}
            SET related_entity_id = ?,
                status = ?,
                completed_at_utc = ?,
                message = ?
            WHERE stage_name = ? AND stage_run_key = ?
            """,
            (
                related_entity_id,
                status,
                utc_now_iso() if completed else None,
                message,
                stage_name,
                stage_run_key,
            ),
        )
    conn.commit()


def run_ingest(
    conn: sqlite3.Connection,
    source_definition: SourceDefinition,
    batch_label: str,
    raw_input_dir: Path,
    ingest_mode: str,
    source_snapshot_ref: str | None = None,
) -> str:
    summary = run_ingest_with_summary(
        conn=conn,
        source_definition=source_definition,
        batch_label=batch_label,
        raw_input_dir=raw_input_dir,
        ingest_mode=ingest_mode,
        source_snapshot_ref=source_snapshot_ref,
    )
    return summary.ingest_batch_id


def run_ingest_with_summary(
    conn: sqlite3.Connection,
    source_definition: SourceDefinition,
    batch_label: str,
    raw_input_dir: Path,
    ingest_mode: str,
    source_snapshot_ref: str | None = None,
) -> IngestExecutionSummary:
    stage_name = "ingest"
    stage_run_key = f"{source_definition.source_id}:{batch_label}"
    ingest_batch_id: str | None = None

    _upsert_pipeline_run(
        conn,
        stage_name=stage_name,
        stage_run_key=stage_run_key,
        related_entity_id=None,
        status="started",
        message="Ingestion started",
        completed=False,
    )

    try:
        register_source(conn, source_definition)

        ingest_batch_id = start_ingest_batch(
            conn=conn,
            source_id=source_definition.source_id,
            batch_label=batch_label,
            ingest_mode=ingest_mode,
            source_snapshot_ref=source_snapshot_ref,
        )

        raw_files = scan_raw_files(raw_input_dir)
        descriptors = [
            build_raw_file_descriptor(
                source_id=source_definition.source_id,
                ingest_batch_id=ingest_batch_id,
                absolute_path=raw_file,
                raw_root_dir=raw_input_dir,
                source_published_at_utc=None,
            )
            for raw_file in raw_files
        ]

        raw_asset_ids = register_raw_assets(conn, descriptors)

        record_count = 0
        for descriptor, raw_asset_id in zip(descriptors, raw_asset_ids, strict=True):
            for _envelope in read_records(
                raw_file=descriptor.absolute_path,
                source_id=source_definition.source_id,
                ingest_batch_id=ingest_batch_id,
                raw_asset_id=raw_asset_id,
            ):
                record_count += 1

        complete_ingest_batch(conn, ingest_batch_id=ingest_batch_id, raw_file_count=len(descriptors))

        summary = IngestExecutionSummary(
            ingest_batch_id=ingest_batch_id,
            file_count=len(descriptors),
            record_count=record_count,
            raw_asset_ids=tuple(raw_asset_ids),
        )

        _upsert_pipeline_run(
            conn,
            stage_name=stage_name,
            stage_run_key=stage_run_key,
            related_entity_id=ingest_batch_id,
            status="completed",
            message=(
                f"Ingestion completed: files={summary.file_count}, "
                f"records={summary.record_count}"
            ),
            completed=True,
        )

        return summary

    except Exception as exc:
        if ingest_batch_id is not None:
            fail_ingest_batch(conn, ingest_batch_id=ingest_batch_id, message=str(exc))

        _upsert_pipeline_run(
            conn,
            stage_name=stage_name,
            stage_run_key=stage_run_key,
            related_entity_id=ingest_batch_id,
            status="failed",
            message=str(exc),
            completed=True,
        )
        raise
