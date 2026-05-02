from __future__ import annotations

import sqlite3

from src.common.clock import utc_now_iso
from src.common.contracts import TABLE_SOURCE_REGISTRY
from src.ingestion.models import SourceDefinition


_CRITICAL_FIELDS = (
    "source_name",
    "source_kind",
    "provider",
    "source_url",
    "license_note",
    "country_scope",
    "is_active",
)


def _diff_source(existing: sqlite3.Row, incoming: SourceDefinition) -> dict[str, tuple[object, object]]:
    diffs: dict[str, tuple[object, object]] = {}
    for field_name in _CRITICAL_FIELDS:
        existing_value = existing[field_name]
        incoming_value = getattr(incoming, field_name)
        if existing_value != incoming_value:
            diffs[field_name] = (existing_value, incoming_value)
    return diffs


def register_source(conn: sqlite3.Connection, source_definition: SourceDefinition) -> None:
    existing = conn.execute(
        f"""
        SELECT source_id, source_name, source_kind, provider, source_url,
               license_note, country_scope, is_active
        FROM {TABLE_SOURCE_REGISTRY}
        WHERE source_id = ?
        """,
        (source_definition.source_id,),
    ).fetchone()

    if existing is None:
        conn.execute(
            f"""
            INSERT INTO {TABLE_SOURCE_REGISTRY} (
                source_id,
                source_name,
                source_kind,
                provider,
                source_url,
                license_note,
                country_scope,
                is_active,
                created_at_utc
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_definition.source_id,
                source_definition.source_name,
                source_definition.source_kind,
                source_definition.provider,
                source_definition.source_url,
                source_definition.license_note,
                source_definition.country_scope,
                source_definition.is_active,
                utc_now_iso(),
            ),
        )
        conn.commit()
        return

    diffs = _diff_source(existing, source_definition)
    if diffs:
        raise ValueError(
            f"Source conflict for source_id={source_definition.source_id!r}. "
            f"Critical fields differ: {diffs}"
        )


def get_source(conn: sqlite3.Connection, source_id: str) -> SourceDefinition | None:
    row = conn.execute(
        f"""
        SELECT source_id, source_name, source_kind, provider, source_url,
               license_note, country_scope, is_active
        FROM {TABLE_SOURCE_REGISTRY}
        WHERE source_id = ?
        """,
        (source_id,),
    ).fetchone()

    if row is None:
        return None

    return SourceDefinition(
        source_id=row["source_id"],
        source_name=row["source_name"],
        source_kind=row["source_kind"],
        provider=row["provider"],
        source_url=row["source_url"],
        license_note=row["license_note"],
        country_scope=row["country_scope"],
        is_active=row["is_active"],
    )
