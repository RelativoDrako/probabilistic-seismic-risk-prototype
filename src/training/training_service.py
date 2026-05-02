from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import joblib

from src.common.clock import utc_now_iso
from src.common.contracts import (
    JOURNAL_STATUS_COMPLETED,
    JOURNAL_STATUS_FAILED,
    JOURNAL_STATUS_STARTED,
    MODEL_FAMILY_LOGISTIC_REGRESSION,
    MODEL_RUN_STATUS_COMPLETED,
    MODEL_RUN_STATUS_FAILED,
    MODEL_RUN_STATUS_STARTED,
    MODEL_SPLIT_POLICY_TEMPORAL,
    WORKFLOW_TRAINING,
)
from src.common.ids import make_journal_id, make_model_run_id
from src.common.logging_utils import get_logger
from src.common.paths import ensure_runtime_dirs, model_artifact_path
from src.common.schema import create_schema
from src.common.settings import get_settings
from src.common.sqlite import managed_connection, transaction

from .dataset import FEATURE_COLUMNS, load_training_rows
from .model_factory import build_model
from .repository import fetch_feature_generation, upsert_model_run
from .splitters import temporal_split


LOGGER = get_logger(__name__)


def _journal_start(connection: sqlite3.Connection, feature_generation_id: str) -> str:
    started_at_utc = utc_now_iso()
    journal_id = make_journal_id(WORKFLOW_TRAINING, "train_baseline_model", started_at_utc)
    connection.execute(
        """
        INSERT OR REPLACE INTO pipeline_run_journal (
            journal_id,
            workflow_name,
            stage_name,
            started_at_utc,
            ended_at_utc,
            status,
            input_ref,
            output_ref,
            notes
        ) VALUES (?, ?, ?, ?, NULL, ?, ?, NULL, NULL)
        """,
        (journal_id, WORKFLOW_TRAINING, "train_baseline_model", started_at_utc, JOURNAL_STATUS_STARTED, feature_generation_id),
    )
    return journal_id


def _journal_finish(connection: sqlite3.Connection, journal_id: str, status: str, output_ref: str | None, notes: str | None) -> None:
    connection.execute(
        """
        UPDATE pipeline_run_journal
        SET ended_at_utc = ?,
            status = ?,
            output_ref = ?,
            notes = ?
        WHERE journal_id = ?
        """,
        (utc_now_iso(), status, output_ref, notes, journal_id),
    )


def _dataset_hash(rows) -> str:
    payload = json.dumps([row.to_dict() for row in rows], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_training(feature_generation_id: str, db_path: str | Path | None = None) -> str:
    settings = get_settings()
    resolved_db_path = create_schema(db_path or settings.db_path)
    ensure_runtime_dirs()
    with managed_connection(resolved_db_path) as connection:
        journal_id = ""
        model_run_id = make_model_run_id(feature_generation_id, MODEL_FAMILY_LOGISTIC_REGRESSION, MODEL_SPLIT_POLICY_TEMPORAL)
        started_at_utc = utc_now_iso()
        feature_generation = fetch_feature_generation(connection, feature_generation_id)
        if feature_generation is None:
            raise ValueError(f"Feature generation not found: {feature_generation_id}")
        try:
            with transaction(connection):
                journal_id = _journal_start(connection, feature_generation_id)
                rows = load_training_rows(connection, feature_generation_id)
                if len(rows) < 4:
                    raise ValueError(f"Not enough feature rows to train model: {len(rows)}")
                train_rows, test_rows = temporal_split(rows)
                if len({row.target_label for row in train_rows}) < 2:
                    raise ValueError("Training split contains only one target class")
                model = build_model()
                X_train = [row.features for row in train_rows]
                y_train = [row.target_label for row in train_rows]
                model.fit(X_train, y_train)
                artifact_path = model_artifact_path(model_run_id)
                artifact_path.parent.mkdir(parents=True, exist_ok=True)
                joblib.dump(
                    {
                        "model": model,
                        "feature_names": FEATURE_COLUMNS,
                        "feature_generation_id": feature_generation_id,
                        "split_policy": MODEL_SPLIT_POLICY_TEMPORAL,
                    },
                    artifact_path,
                )
                upsert_model_run(
                    connection,
                    model_run_id=model_run_id,
                    feature_generation_id=feature_generation_id,
                    feature_set_version=feature_generation["feature_set_version"],
                    model_family=MODEL_FAMILY_LOGISTIC_REGRESSION,
                    split_policy=MODEL_SPLIT_POLICY_TEMPORAL,
                    train_row_count=len(train_rows),
                    test_row_count=len(test_rows),
                    model_artifact_path=str(artifact_path),
                    dataset_hash=_dataset_hash(rows),
                    status=MODEL_RUN_STATUS_COMPLETED,
                    started_at_utc=started_at_utc,
                    completed_at_utc=utc_now_iso(),
                    params_json=json.dumps({"feature_names": FEATURE_COLUMNS}, sort_keys=True),
                )
                _journal_finish(connection, journal_id, JOURNAL_STATUS_COMPLETED, model_run_id, f"train={len(train_rows)} test={len(test_rows)}")
            LOGGER.info(
                "model_training_completed",
                extra={
                    "model_run_id": model_run_id,
                    "feature_generation_id": feature_generation_id,
                    "db_path": str(resolved_db_path),
                },
            )
            return model_run_id
        except Exception as exc:
            with transaction(connection):
                upsert_model_run(
                    connection,
                    model_run_id=model_run_id,
                    feature_generation_id=feature_generation_id,
                    feature_set_version=feature_generation["feature_set_version"],
                    model_family=MODEL_FAMILY_LOGISTIC_REGRESSION,
                    split_policy=MODEL_SPLIT_POLICY_TEMPORAL,
                    train_row_count=0,
                    test_row_count=0,
                    model_artifact_path=str(model_artifact_path(model_run_id)),
                    dataset_hash="",
                    status=MODEL_RUN_STATUS_FAILED,
                    started_at_utc=started_at_utc,
                    completed_at_utc=utc_now_iso(),
                    params_json=json.dumps({"feature_names": FEATURE_COLUMNS}, sort_keys=True),
                )
                if journal_id:
                    _journal_finish(connection, journal_id, JOURNAL_STATUS_FAILED, model_run_id, str(exc))
            LOGGER.exception("model_training_failed", extra={"model_run_id": model_run_id, "db_path": str(resolved_db_path)})
            raise
