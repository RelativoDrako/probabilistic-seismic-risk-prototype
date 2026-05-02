from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

from src.common.settings import load_settings
from src.common.sqlite import connect_sqlite
from src.visualization.demo_report import write_demo_evidence_json, write_demo_evidence_md
from src.visualization.evaluation_panels import export_metrics_panel, export_model_summary_panel
from src.visualization.magnitude_distribution import export_magnitude_distribution
from src.visualization.pipeline_trace import export_pipeline_trace
from src.visualization.regional_counts import export_regional_event_counts
from src.visualization.risk_heatmap import export_risk_heatmap
from src.visualization.risk_map import export_probabilistic_risk_map


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export demo visual assets from pipeline evidence.")
    parser.add_argument("--ingest-batch-id", required=True)
    parser.add_argument("--feature-set-version", required=True)
    parser.add_argument("--output-dir", default=None)
    return parser


def _safe_export(export_name: str, export_fn, output_path: Path, *args, **kwargs) -> tuple[str, str]:
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result_path = export_fn(*args, output_path=output_path, **kwargs)
        if caught:
            print(f"[warn] {export_name}_warnings={len(caught)}")
        print(f"[ok] {export_name}={Path(result_path).as_posix()}")
        return export_name, Path(result_path).as_posix()
    except Exception as exc:
        print(f"[warn] {export_name}_failed={exc}")
        return export_name, ""


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings()

    base_output_dir = Path(args.output_dir).resolve() if args.output_dir else settings.artifacts_dir
    plots_dir = base_output_dir / "plots"
    reports_dir = base_output_dir / "reports"
    models_dir = settings.artifacts_dir / "models"

    with connect_sqlite(settings.sqlite_path) as conn:
        raw_files_count = conn.execute(
            "SELECT COUNT(*) AS total FROM raw_asset_manifest WHERE ingest_batch_id = ?",
            (args.ingest_batch_id,),
        ).fetchone()["total"]

        curated_rows = conn.execute(
            """
            SELECT *
            FROM curated_events
            WHERE ingest_batch_id = ? AND record_status = 'accepted'
            ORDER BY occurred_at_utc
            """,
            (args.ingest_batch_id,),
        ).fetchall()
        curated_events = [dict(r) for r in curated_rows]

        feature_generation_row = conn.execute(
            """
            SELECT feature_generation_id
            FROM feature_generations
            WHERE source_batch_scope = ? AND feature_set_version = ?
            ORDER BY started_at_utc DESC
            LIMIT 1
            """,
            (args.ingest_batch_id, args.feature_set_version),
        ).fetchone()
        feature_generation_id = None if feature_generation_row is None else feature_generation_row["feature_generation_id"]

        feature_rows = []
        if feature_generation_id is not None:
            rows = conn.execute(
                "SELECT * FROM region_features WHERE feature_generation_id = ? ORDER BY region_code",
                (feature_generation_id,),
            ).fetchall()
            feature_rows = [dict(r) for r in rows]

    metrics_path = settings.artifacts_dir / "reports" / "metrics.json"
    metrics_payload = {}
    if metrics_path.exists():
        metrics_payload = json.loads(metrics_path.read_text(encoding="utf-8"))

    region_counts = {}
    magnitudes = []
    for event in curated_events:
        region_counts[event["region_code"]] = region_counts.get(event["region_code"], 0) + 1
        if event.get("magnitude_value") is not None:
            magnitudes.append(float(event["magnitude_value"]))

    region_scores = {}
    for row in feature_rows:
        region_scores[row["region_code"]] = float(row.get("event_count") or 0) + float(row.get("mean_magnitude") or 0)

    exports = dict([
        _safe_export(
            "pipeline_trace",
            export_pipeline_trace,
            plots_dir / "pipeline_trace.png",
            raw_assets_count=int(raw_files_count),
            curated_events_count=len(curated_events),
            feature_rows_count=len(feature_rows),
            has_model_artifact=(models_dir / "baseline_model.joblib").exists(),
            has_metrics_report=metrics_path.exists(),
        ),
        _safe_export("regional_event_counts", export_regional_event_counts, plots_dir / "regional_event_counts.png", region_counts),
        _safe_export("magnitude_distribution", export_magnitude_distribution, plots_dir / "magnitude_distribution.png", magnitudes),
        _safe_export("risk_heatmap", export_risk_heatmap, plots_dir / "risk_heatmap.png", feature_rows),
        _safe_export("probabilistic_risk_map", export_probabilistic_risk_map, plots_dir / "probabilistic_risk_map.png", region_scores),
        _safe_export("metrics_panel", export_metrics_panel, plots_dir / "metrics_panel.png", metrics_payload or {"model": "n/a"}),
        _safe_export(
            "model_summary_panel",
            export_model_summary_panel,
            plots_dir / "model_summary_panel.png",
            {
                "ingest_batch_id": args.ingest_batch_id,
                "feature_set_version": args.feature_set_version,
                "dataset_rows": metrics_payload.get("dataset_rows", "n/a"),
                "train_rows": metrics_payload.get("train_rows", "n/a"),
                "test_rows": metrics_payload.get("test_rows", "n/a"),
                "split_rule": metrics_payload.get("split_rule", "n/a"),
                "target_definition": metrics_payload.get("target_definition", "n/a"),
            },
        ),
    ])

    payload = {
        "source_id": "prototype_source",
        "ingest_batch_id": args.ingest_batch_id,
        "feature_set_version": args.feature_set_version,
        "raw_files_count": int(raw_files_count),
        "curated_events_count": len(curated_events),
        "feature_generation_id": feature_generation_id,
        "model_artifact": str((models_dir / "baseline_model.joblib").as_posix()),
        "metrics_path": str(metrics_path.as_posix()),
        "plots": [p for p in exports.values() if p],
        "plot_status": exports,
    }

    md_path = write_demo_evidence_md(payload, reports_dir / "demo_evidence.md")
    json_path = write_demo_evidence_json(payload, reports_dir / "demo_evidence.json")

    print(f"[ok] plots_dir={plots_dir.as_posix()}")
    print(f"[ok] demo_evidence_md={md_path.as_posix()}")
    print(f"[ok] demo_evidence_json={json_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
