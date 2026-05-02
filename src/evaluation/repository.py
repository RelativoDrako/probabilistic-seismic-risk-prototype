from __future__ import annotations

import sqlite3


def upsert_evaluation_report(
    connection: sqlite3.Connection,
    *,
    evaluation_report_id: str,
    model_run_id: str,
    report_json_path: str,
    report_md_path: str,
    roc_plot_path: str,
    pr_plot_path: str,
    prob_hist_path: str,
    roc_auc: float,
    pr_auc: float,
    precision: float,
    recall: float,
    f1: float,
    brier_score: float,
    created_at_utc: str,
) -> None:
    connection.execute(
        """
        INSERT INTO evaluation_reports (
            evaluation_id,
            run_id,
            report_path,
            metrics_json_path,
            roc_auc,
            pr_auc,
            f1_score,
            brier_score,
            created_at_utc,
            model_run_id,
            report_json_path,
            report_md_path,
            roc_plot_path,
            pr_plot_path,
            prob_hist_path,
            precision,
            recall
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(evaluation_id) DO UPDATE SET
            run_id = excluded.run_id,
            report_path = excluded.report_path,
            metrics_json_path = excluded.metrics_json_path,
            roc_auc = excluded.roc_auc,
            pr_auc = excluded.pr_auc,
            f1_score = excluded.f1_score,
            brier_score = excluded.brier_score,
            created_at_utc = excluded.created_at_utc,
            model_run_id = excluded.model_run_id,
            report_json_path = excluded.report_json_path,
            report_md_path = excluded.report_md_path,
            roc_plot_path = excluded.roc_plot_path,
            pr_plot_path = excluded.pr_plot_path,
            prob_hist_path = excluded.prob_hist_path,
            precision = excluded.precision,
            recall = excluded.recall
        """,
        (
            evaluation_report_id,
            model_run_id,
            report_md_path,
            report_json_path,
            roc_auc,
            pr_auc,
            f1,
            brier_score,
            created_at_utc,
            model_run_id,
            report_json_path,
            report_md_path,
            roc_plot_path,
            pr_plot_path,
            prob_hist_path,
            precision,
            recall,
        ),
    )


def fetch_latest_evaluation(connection: sqlite3.Connection) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT *
        FROM evaluation_reports
        ORDER BY created_at_utc DESC, evaluation_id DESC
        LIMIT 1
        """
    ).fetchone()
