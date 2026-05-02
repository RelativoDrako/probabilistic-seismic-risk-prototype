from __future__ import annotations

import sqlite3


def fetch_feature_generation(connection: sqlite3.Connection, feature_generation_id: str) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT generation_id, feature_set_version, source_batch_id, status, created_at_utc, notes, window_spec
        FROM feature_generations
        WHERE generation_id = ?
        LIMIT 1
        """,
        (feature_generation_id,),
    ).fetchone()


def upsert_model_run(
    connection: sqlite3.Connection,
    *,
    model_run_id: str,
    feature_generation_id: str,
    feature_set_version: str,
    model_family: str,
    split_policy: str,
    train_row_count: int,
    test_row_count: int,
    model_artifact_path: str,
    dataset_hash: str,
    status: str,
    started_at_utc: str,
    completed_at_utc: str | None,
    params_json: str,
) -> None:
    connection.execute(
        """
        INSERT INTO model_runs (
            run_id,
            model_name,
            feature_set_version,
            train_start_utc,
            train_end_utc,
            status,
            dataset_hash,
            params_json,
            artifact_path,
            notes,
            feature_generation_id,
            model_family,
            split_policy,
            train_row_count,
            test_row_count,
            model_artifact_path,
            started_at_utc,
            completed_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_id) DO UPDATE SET
            status = excluded.status,
            dataset_hash = excluded.dataset_hash,
            params_json = excluded.params_json,
            artifact_path = excluded.artifact_path,
            notes = excluded.notes,
            feature_generation_id = excluded.feature_generation_id,
            model_family = excluded.model_family,
            split_policy = excluded.split_policy,
            train_row_count = excluded.train_row_count,
            test_row_count = excluded.test_row_count,
            model_artifact_path = excluded.model_artifact_path,
            train_end_utc = excluded.train_end_utc,
            completed_at_utc = excluded.completed_at_utc
        """,
        (
            model_run_id,
            model_family,
            feature_set_version,
            started_at_utc,
            completed_at_utc,
            status,
            dataset_hash,
            params_json,
            model_artifact_path,
            None,
            feature_generation_id,
            model_family,
            split_policy,
            train_row_count,
            test_row_count,
            model_artifact_path,
            started_at_utc,
            completed_at_utc,
        ),
    )


def fetch_model_run(connection: sqlite3.Connection, model_run_id: str) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT *
        FROM model_runs
        WHERE run_id = ?
        LIMIT 1
        """,
        (model_run_id,),
    ).fetchone()


def fetch_latest_model_run(connection: sqlite3.Connection) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT *
        FROM model_runs
        ORDER BY COALESCE(completed_at_utc, train_end_utc, started_at_utc, train_start_utc) DESC, run_id DESC
        LIMIT 1
        """
    ).fetchone()
