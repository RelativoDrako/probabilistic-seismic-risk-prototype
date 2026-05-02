from __future__ import annotations

from pathlib import Path

from .paths import canonical_db_path
from .settings import get_settings
from .sqlite import managed_connection, transaction


TABLE_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS source_registry (
        source_id TEXT PRIMARY KEY,
        source_name TEXT NOT NULL UNIQUE,
        source_role TEXT NOT NULL,
        base_url TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        notes TEXT,
        created_at_utc TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS ingest_batches (
        batch_id TEXT PRIMARY KEY,
        source_id TEXT NOT NULL,
        scope_hash TEXT NOT NULL,
        start_time_utc TEXT,
        end_time_utc TEXT,
        retrieved_at_utc TEXT NOT NULL,
        record_count INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL,
        raw_manifest_path TEXT,
        notes TEXT,
        FOREIGN KEY (source_id) REFERENCES source_registry (source_id),
        UNIQUE (source_id, scope_hash)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS raw_asset_manifest (
        manifest_id TEXT PRIMARY KEY,
        batch_id TEXT NOT NULL,
        source_id TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_format TEXT NOT NULL,
        sha256 TEXT NOT NULL UNIQUE,
        schema_version TEXT NOT NULL,
        created_at_utc TEXT NOT NULL,
        record_count INTEGER,
        file_size_bytes INTEGER NOT NULL,
        FOREIGN KEY (batch_id) REFERENCES ingest_batches (batch_id),
        FOREIGN KEY (source_id) REFERENCES source_registry (source_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS curated_events (
        event_id TEXT PRIMARY KEY,
        source_event_id TEXT,
        source_id TEXT NOT NULL,
        batch_id TEXT NOT NULL,
        event_time_utc TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        depth_km REAL,
        magnitude REAL,
        magnitude_type TEXT,
        place_text TEXT,
        state_name TEXT NOT NULL,
        acceptance_status TEXT NOT NULL,
        raw_manifest_id TEXT,
        inserted_at_utc TEXT NOT NULL,
        FOREIGN KEY (source_id) REFERENCES source_registry (source_id),
        FOREIGN KEY (batch_id) REFERENCES ingest_batches (batch_id),
        FOREIGN KEY (raw_manifest_id) REFERENCES raw_asset_manifest (manifest_id),
        UNIQUE (source_id, source_event_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS feature_generations (
        generation_id TEXT PRIMARY KEY,
        feature_set_version TEXT NOT NULL,
        source_batch_id TEXT,
        status TEXT NOT NULL,
        created_at_utc TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (source_batch_id) REFERENCES ingest_batches (batch_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS region_features (
        feature_row_id TEXT PRIMARY KEY,
        generation_id TEXT,
        region_name TEXT NOT NULL,
        window_start_utc TEXT NOT NULL,
        window_end_utc TEXT NOT NULL,
        event_count INTEGER NOT NULL,
        mean_magnitude REAL,
        max_magnitude REAL,
        mean_depth_km REAL,
        recent_rate_7d REAL,
        recent_rate_30d REAL,
        rolling_delta_rate REAL,
        target_risk_label INTEGER,
        target_risk_score REAL,
        feature_set_version TEXT NOT NULL,
        created_at_utc TEXT NOT NULL,
        FOREIGN KEY (generation_id) REFERENCES feature_generations (generation_id),
        UNIQUE (region_name, window_start_utc, window_end_utc, feature_set_version)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS model_runs (
        run_id TEXT PRIMARY KEY,
        model_name TEXT NOT NULL,
        feature_set_version TEXT NOT NULL,
        train_start_utc TEXT NOT NULL,
        train_end_utc TEXT,
        status TEXT NOT NULL,
        dataset_hash TEXT,
        params_json TEXT,
        artifact_path TEXT,
        notes TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS evaluation_reports (
        evaluation_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        report_path TEXT NOT NULL,
        metrics_json_path TEXT NOT NULL,
        roc_auc REAL,
        pr_auc REAL,
        f1_score REAL,
        brier_score REAL,
        created_at_utc TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES model_runs (run_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS pipeline_run_journal (
        journal_id TEXT PRIMARY KEY,
        workflow_name TEXT NOT NULL,
        stage_name TEXT NOT NULL,
        started_at_utc TEXT NOT NULL,
        ended_at_utc TEXT,
        status TEXT NOT NULL,
        input_ref TEXT,
        output_ref TEXT,
        notes TEXT
    );
    """,
]

INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_ingest_batches_source_status ON ingest_batches (source_id, status);",
    "CREATE INDEX IF NOT EXISTS idx_raw_asset_manifest_batch_id ON raw_asset_manifest (batch_id);",
    "CREATE INDEX IF NOT EXISTS idx_curated_events_batch_id ON curated_events (batch_id);",
    "CREATE INDEX IF NOT EXISTS idx_curated_events_event_time ON curated_events (event_time_utc);",
    "CREATE INDEX IF NOT EXISTS idx_curated_events_state_time ON curated_events (state_name, event_time_utc);",
    "CREATE INDEX IF NOT EXISTS idx_region_features_region_window ON region_features (region_name, window_start_utc, window_end_utc);",
    "CREATE INDEX IF NOT EXISTS idx_region_features_generation ON region_features (generation_id);",
    "CREATE INDEX IF NOT EXISTS idx_pipeline_run_journal_workflow_stage ON pipeline_run_journal (workflow_name, stage_name, started_at_utc);",
]

REQUIRED_COLUMNS = {
    "source_registry": {
        "source_id": "TEXT",
        "source_name": "TEXT",
        "source_role": "TEXT",
        "base_url": "TEXT",
        "is_active": "INTEGER",
        "notes": "TEXT",
        "created_at_utc": "TEXT",
    },
    "ingest_batches": {
        "batch_id": "TEXT",
        "source_id": "TEXT",
        "scope_hash": "TEXT",
        "start_time_utc": "TEXT",
        "end_time_utc": "TEXT",
        "retrieved_at_utc": "TEXT",
        "record_count": "INTEGER",
        "status": "TEXT",
        "raw_manifest_path": "TEXT",
        "notes": "TEXT",
    },
    "raw_asset_manifest": {
        "manifest_id": "TEXT",
        "batch_id": "TEXT",
        "source_id": "TEXT",
        "file_path": "TEXT",
        "file_name": "TEXT",
        "file_format": "TEXT",
        "sha256": "TEXT",
        "schema_version": "TEXT",
        "created_at_utc": "TEXT",
        "record_count": "INTEGER",
        "file_size_bytes": "INTEGER",
    },
    "curated_events": {
        "event_id": "TEXT",
        "source_event_id": "TEXT",
        "source_id": "TEXT",
        "batch_id": "TEXT",
        "event_time_utc": "TEXT",
        "latitude": "REAL",
        "longitude": "REAL",
        "depth_km": "REAL",
        "magnitude": "REAL",
        "magnitude_type": "TEXT",
        "place_text": "TEXT",
        "state_name": "TEXT",
        "acceptance_status": "TEXT",
        "raw_manifest_id": "TEXT",
        "inserted_at_utc": "TEXT",
    },
    "feature_generations": {
        "generation_id": "TEXT",
        "feature_set_version": "TEXT",
        "source_batch_id": "TEXT",
        "status": "TEXT",
        "created_at_utc": "TEXT",
        "notes": "TEXT",
        "window_spec": "TEXT",
    },
    "region_features": {
        "feature_row_id": "TEXT",
        "generation_id": "TEXT",
        "region_name": "TEXT",
        "window_start_utc": "TEXT",
        "window_end_utc": "TEXT",
        "event_count": "INTEGER",
        "mean_magnitude": "REAL",
        "max_magnitude": "REAL",
        "mean_depth_km": "REAL",
        "recent_rate_7d": "REAL",
        "recent_rate_30d": "REAL",
        "rolling_delta_rate": "REAL",
        "target_risk_label": "INTEGER",
        "target_risk_score": "REAL",
        "feature_set_version": "TEXT",
        "created_at_utc": "TEXT",
        "region_code": "TEXT",
        "days_since_last_event": "REAL",
        "target_label": "REAL",
    },
    "model_runs": {
        "run_id": "TEXT",
        "model_name": "TEXT",
        "feature_set_version": "TEXT",
        "train_start_utc": "TEXT",
        "train_end_utc": "TEXT",
        "status": "TEXT",
        "dataset_hash": "TEXT",
        "params_json": "TEXT",
        "artifact_path": "TEXT",
        "notes": "TEXT",
        "feature_generation_id": "TEXT",
        "model_family": "TEXT",
        "split_policy": "TEXT",
        "train_row_count": "INTEGER",
        "test_row_count": "INTEGER",
        "model_artifact_path": "TEXT",
        "started_at_utc": "TEXT",
        "completed_at_utc": "TEXT",
    },
    "evaluation_reports": {
        "evaluation_id": "TEXT",
        "run_id": "TEXT",
        "report_path": "TEXT",
        "metrics_json_path": "TEXT",
        "roc_auc": "REAL",
        "pr_auc": "REAL",
        "f1_score": "REAL",
        "brier_score": "REAL",
        "created_at_utc": "TEXT",
        "model_run_id": "TEXT",
        "report_json_path": "TEXT",
        "report_md_path": "TEXT",
        "roc_plot_path": "TEXT",
        "pr_plot_path": "TEXT",
        "prob_hist_path": "TEXT",
        "precision": "REAL",
        "recall": "REAL",
    },
    "pipeline_run_journal": {
        "journal_id": "TEXT",
        "workflow_name": "TEXT",
        "stage_name": "TEXT",
        "started_at_utc": "TEXT",
        "ended_at_utc": "TEXT",
        "status": "TEXT",
        "input_ref": "TEXT",
        "output_ref": "TEXT",
        "notes": "TEXT",
    },
}


def _existing_tables(connection) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return {row["name"] for row in rows}


def _existing_columns(connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def _ensure_required_columns(connection) -> None:
    existing_tables = _existing_tables(connection)
    for table_name, columns in REQUIRED_COLUMNS.items():
        if table_name not in existing_tables:
            continue
        existing = _existing_columns(connection, table_name)
        for column_name, definition in columns.items():
            if column_name in existing:
                continue
            connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def create_schema(db_path: str | Path | None = None) -> Path:
    settings = get_settings()
    resolved_db_path = Path(db_path).expanduser().resolve() if db_path else settings.db_path
    with managed_connection(resolved_db_path) as connection:
        with transaction(connection):
            for statement in TABLE_STATEMENTS:
                connection.execute(statement)
            _ensure_required_columns(connection)
            for statement in INDEX_STATEMENTS:
                connection.execute(statement)
    return resolved_db_path


def bootstrap_schema() -> Path:
    return create_schema(canonical_db_path())
