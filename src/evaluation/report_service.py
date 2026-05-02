from __future__ import annotations

import json
from pathlib import Path

import joblib

from src.common.clock import utc_now_iso
from src.common.contracts import JOURNAL_STATUS_COMPLETED, JOURNAL_STATUS_FAILED, JOURNAL_STATUS_STARTED, WORKFLOW_EVALUATION
from src.common.ids import make_evaluation_report_id, make_journal_id
from src.common.logging_utils import get_logger
from src.common.paths import (
    ensure_runtime_dirs,
    evaluation_json_path,
    evaluation_markdown_path,
    pr_plot_path,
    probability_histogram_path,
    roc_plot_path,
)
from src.common.schema import create_schema
from src.common.settings import get_settings
from src.common.sqlite import managed_connection, transaction
from src.training.dataset import load_training_rows
from src.training.repository import fetch_model_run
from src.training.splitters import temporal_split

from .metrics import compute_curves, compute_metrics
from .plots import save_pr_curve, save_probability_histogram, save_roc_curve
from .repository import upsert_evaluation_report


LOGGER = get_logger(__name__)


def _journal_start(connection, model_run_id: str) -> str:
    started_at_utc = utc_now_iso()
    journal_id = make_journal_id(WORKFLOW_EVALUATION, "evaluate_model_run", started_at_utc)
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
        (journal_id, WORKFLOW_EVALUATION, "evaluate_model_run", started_at_utc, JOURNAL_STATUS_STARTED, model_run_id),
    )
    return journal_id


def _journal_finish(connection, journal_id: str, status: str, output_ref: str | None, notes: str | None) -> None:
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


def run_evaluation(model_run_id: str, db_path: str | Path | None = None) -> str:
    settings = get_settings()
    resolved_db_path = create_schema(db_path or settings.db_path)
    ensure_runtime_dirs()
    with managed_connection(resolved_db_path) as connection:
        journal_id = ""
        evaluation_report_id = make_evaluation_report_id(model_run_id)
        try:
            model_run = fetch_model_run(connection, model_run_id)
            if model_run is None:
                raise ValueError(f"Model run not found: {model_run_id}")
            feature_generation_id = model_run["feature_generation_id"]
            artifact_path = model_run["model_artifact_path"] or model_run["artifact_path"]
            if not feature_generation_id:
                raise ValueError(f"Model run missing feature_generation_id: {model_run_id}")
            if not artifact_path:
                raise ValueError(f"Model run missing model artifact path: {model_run_id}")
            bundle = joblib.load(artifact_path)
            model = bundle["model"]
            with transaction(connection):
                journal_id = _journal_start(connection, model_run_id)
                rows = load_training_rows(connection, feature_generation_id)
                train_rows, test_rows = temporal_split(rows)
                if len({row.target_label for row in test_rows}) < 2:
                    raise ValueError("Evaluation split contains only one target class")
                X_test = [row.features for row in test_rows]
                y_test = [row.target_label for row in test_rows]
                probabilities = [float(value) for value in model.predict_proba(X_test)[:, 1]]
                metrics = compute_metrics(y_test, probabilities)
                curves = compute_curves(y_test, probabilities)

                json_path = evaluation_json_path(evaluation_report_id)
                md_path = evaluation_markdown_path(evaluation_report_id)
                roc_path = roc_plot_path(evaluation_report_id)
                pr_path = pr_plot_path(evaluation_report_id)
                hist_path = probability_histogram_path(evaluation_report_id)
                for target in (json_path, md_path, roc_path, pr_path, hist_path):
                    target.parent.mkdir(parents=True, exist_ok=True)

                report_payload = {
                    "evaluation_report_id": evaluation_report_id,
                    "model_run_id": model_run_id,
                    "feature_generation_id": feature_generation_id,
                    "metrics": metrics,
                    "test_row_count": len(test_rows),
                    "feature_names": bundle.get("feature_names", []),
                }
                json_path.write_text(json.dumps(report_payload, indent=2, sort_keys=True), encoding="utf-8")
                md_path.write_text(
                    "\n".join(
                        [
                            "# Evaluation Report",
                            "",
                            f"- evaluation_report_id: `{evaluation_report_id}`",
                            f"- model_run_id: `{model_run_id}`",
                            f"- feature_generation_id: `{feature_generation_id}`",
                            f"- test_row_count: `{len(test_rows)}`",
                            "",
                            "## Metrics",
                            "",
                            *(f"- {name}: `{value:.6f}`" for name, value in metrics.items()),
                        ]
                    ),
                    encoding="utf-8",
                )
                save_roc_curve(roc_path, curves["roc_fpr"], curves["roc_tpr"])
                save_pr_curve(pr_path, curves["pr_recall"], curves["pr_precision"])
                save_probability_histogram(hist_path, probabilities)
                upsert_evaluation_report(
                    connection,
                    evaluation_report_id=evaluation_report_id,
                    model_run_id=model_run_id,
                    report_json_path=str(json_path),
                    report_md_path=str(md_path),
                    roc_plot_path=str(roc_path),
                    pr_plot_path=str(pr_path),
                    prob_hist_path=str(hist_path),
                    roc_auc=metrics["roc_auc"],
                    pr_auc=metrics["pr_auc"],
                    precision=metrics["precision"],
                    recall=metrics["recall"],
                    f1=metrics["f1"],
                    brier_score=metrics["brier_score"],
                    created_at_utc=utc_now_iso(),
                )
                _journal_finish(connection, journal_id, JOURNAL_STATUS_COMPLETED, evaluation_report_id, f"test={len(test_rows)}")
            LOGGER.info(
                "evaluation_completed",
                extra={
                    "evaluation_report_id": evaluation_report_id,
                    "model_run_id": model_run_id,
                    "db_path": str(resolved_db_path),
                },
            )
            return evaluation_report_id
        except Exception as exc:
            with transaction(connection):
                if journal_id:
                    _journal_finish(connection, journal_id, JOURNAL_STATUS_FAILED, evaluation_report_id, str(exc))
            LOGGER.exception("evaluation_failed", extra={"evaluation_report_id": evaluation_report_id, "db_path": str(resolved_db_path)})
            raise
