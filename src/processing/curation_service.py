from __future__ import annotations

import sqlite3
from pathlib import Path

from src.common.clock import utc_now_iso
from src.common.ids import build_event_id, build_pipeline_run_id
from src.processing.deduplication import detect_duplicate
from src.processing.geo_enrichment import resolve_region_code, resolve_municipality_code
from src.processing.models import CuratedEventRecord
from src.processing.normalizers import build_candidate_event
from src.processing.repository import upsert_curated_events
from src.processing.validators import validate_candidate_event, is_accept_event
from src.ingestion.readers.ssn_reader import read_records


def _journal_start(conn: sqlite3.Connection, stage_name: str, stage_run_key: str, related_entity_id: str | None) -> None:
    conn.execute(
        """
        INSERT INTO pipeline_run_journal (
            pipeline_run_id, stage_name, stage_run_key, related_entity_id,
            status, started_at_utc, completed_at_utc, message
        )
        VALUES (?, ?, ?, ?, 'started', ?, NULL, ?)
        ON CONFLICT(stage_name, stage_run_key) DO UPDATE SET
            status='started',
            related_entity_id=excluded.related_entity_id,
            started_at_utc=excluded.started_at_utc,
            completed_at_utc=NULL,
            message=excluded.message
        """,
        (
            build_pipeline_run_id(stage_name, stage_run_key),
            stage_name,
            stage_run_key,
            related_entity_id,
            utc_now_iso(),
            "curation started",
        ),
    )
    conn.commit()


def _journal_finish(conn: sqlite3.Connection, stage_name: str, stage_run_key: str, related_entity_id: str | None, status: str, message: str) -> None:
    conn.execute(
        """
        UPDATE pipeline_run_journal
        SET related_entity_id = ?, status = ?, completed_at_utc = ?, message = ?
        WHERE stage_name = ? AND stage_run_key = ?
        """,
        (related_entity_id, status, utc_now_iso(), message, stage_name, stage_run_key),
    )
    conn.commit()


def _unpack_raw_asset(raw_asset) -> tuple[str, str]:
    if isinstance(raw_asset, sqlite3.Row):
        return raw_asset["raw_asset_id"], raw_asset["relative_path"]
    if isinstance(raw_asset, dict):
        return raw_asset["raw_asset_id"], raw_asset["relative_path"]
    if isinstance(raw_asset, (tuple, list)) and len(raw_asset) >= 2:
        return raw_asset[0], raw_asset[1]
    raise TypeError(f"Unsupported raw_asset type: {type(raw_asset)!r}")


def _resolve_raw_file_path(repo_root: Path, relative_path: str) -> Path | None:
    raw_root = repo_root / "data" / "raw"
    rel_path = Path(relative_path)

    direct = raw_root / rel_path
    if direct.exists() and direct.is_file():
        return direct

    matches: list[Path] = []
    for candidate in raw_root.rglob(rel_path.name):
        if not candidate.is_file():
            continue
        if "_meta" in candidate.parts:
            continue
        matches.append(candidate)

    if len(matches) == 1:
        return matches[0]

    rel_suffix = rel_path.as_posix()
    for candidate in matches:
        candidate_rel = candidate.relative_to(raw_root).as_posix()
        if candidate_rel.endswith(rel_suffix):
            return candidate

    return None


def curate_ingest_batch(conn: sqlite3.Connection, source_id: str, ingest_batch_id: str, curation_version: str) -> dict:
    stage_name = "curate"
    stage_run_key = ingest_batch_id
    _journal_start(conn, stage_name, stage_run_key, ingest_batch_id)

    batch_row = conn.execute(
        """
        SELECT ingest_batch_id
        FROM ingest_batches
        WHERE ingest_batch_id = ? AND source_id = ?
        """,
        (ingest_batch_id, source_id),
    ).fetchone()
    if batch_row is None:
        raise ValueError(f"Ingest batch not found for source_id={source_id!r}, ingest_batch_id={ingest_batch_id!r}")

    raw_assets = conn.execute(
        """
        SELECT raw_asset_id, relative_path
        FROM raw_asset_manifest
        WHERE ingest_batch_id = ?
        ORDER BY relative_path
        """,
        (ingest_batch_id,),
    ).fetchall()

    print(f"[debug] raw_assets_found={len(raw_assets)}")
    print(f"[debug] sample_asset={raw_assets[0] if raw_assets else None}")

    if not raw_assets:
        _journal_finish(conn, stage_name, stage_run_key, ingest_batch_id, "completed", "No raw assets found")
        return {
            "processed_total": 0,
            "accepted_total": 0,
            "rejected_total": 0,
            "deduplicated_total": 0,
        }

    repo_root = Path(__file__).resolve().parents[2]
    rows: list[CuratedEventRecord] = []
    processed_total = 0
    accepted_total = 0
    rejected_total = 0
    deduplicated_total = 0

    for raw_asset in raw_assets:
        raw_asset_id, relative_path = _unpack_raw_asset(raw_asset)

        if Path(relative_path).suffix.lower() != ".csv":
            print(f"[info] skipped_non_csv_asset={relative_path}")
            continue

        raw_file_path = _resolve_raw_file_path(repo_root, relative_path)
        if raw_file_path is None:
            print(f"[warn] missing_raw_file={repo_root / 'data' / 'raw' / relative_path}")
            print(f"[warn] missing_raw_file_alt_search=name:{Path(relative_path).name}")
            continue

        print(f"[debug] resolved_raw_file={raw_file_path}")

        for envelope in read_records(
            raw_file=raw_file_path,
            source_id=source_id,
            ingest_batch_id=ingest_batch_id,
            raw_asset_id=raw_asset_id,
        ):
            processed_total += 1
            candidate = build_candidate_event(envelope)

            if candidate.region_code is None and candidate.latitude is not None and candidate.longitude is not None:
                region_code = resolve_region_code(candidate.latitude, candidate.longitude)
                municipality_code = resolve_municipality_code(candidate.latitude, candidate.longitude)
                candidate = candidate.__class__(
                    **{
                        **candidate.__dict__,
                        "region_code": region_code,
                        "municipality_code": municipality_code,
                    }
                )

            issues = validate_candidate_event(candidate)
            if not is_accept_event(issues):
                rejected_total += 1
                continue

            duplicate_event_id = detect_duplicate(conn, candidate, curation_version)
            if duplicate_event_id is not None:
                deduplicated_total += 1
                continue

            event_id = build_event_id(
                source_id=candidate.source_id,
                source_event_key=candidate.source_event_key,
                occurred_at_utc=candidate.occurred_at_utc,
                latitude=candidate.latitude,
                longitude=candidate.longitude,
            )
            now = utc_now_iso()
            rows.append(
                CuratedEventRecord(
                    event_id=event_id,
                    source_id=candidate.source_id,
                    ingest_batch_id=candidate.ingest_batch_id,
                    source_event_key=candidate.source_event_key,
                    occurred_at_utc=candidate.occurred_at_utc,
                    latitude=candidate.latitude,
                    longitude=candidate.longitude,
                    depth_km=candidate.depth_km,
                    magnitude_value=candidate.magnitude_value,
                    magnitude_type=candidate.magnitude_type,
                    region_code=candidate.region_code,
                    municipality_code=candidate.municipality_code,
                    curation_version=curation_version,
                    record_status="accepted",
                    raw_asset_id=candidate.raw_asset_id,
                    inserted_at_utc=now,
                    updated_at_utc=now,
                    rejection_reason=None,
                )
            )
            accepted_total += 1

    upsert_curated_events(conn, rows)
    _journal_finish(
        conn,
        stage_name,
        stage_run_key,
        ingest_batch_id,
        "completed",
        f"processed={processed_total}, accepted={accepted_total}, rejected={rejected_total}, deduplicated={deduplicated_total}",
    )
    return {
        "processed_total": processed_total,
        "accepted_total": accepted_total,
        "rejected_total": rejected_total,
        "deduplicated_total": deduplicated_total,
    }
