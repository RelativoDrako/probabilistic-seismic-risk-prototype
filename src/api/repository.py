from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.common.settings import get_settings
from src.common.schema import create_schema
from src.common.sqlite import managed_connection


REFERENCE_GEOGRAPHIES: list[dict[str, Any]] = [
    {
        "label": "Baja California / Gulf of California",
        "political_division": "Baja California, Baja California Sur, Sonora",
        "latitude": 29.5,
        "longitude": -114.5,
        "tectonic_layer": "Gulf of California extensional corridor",
    },
    {
        "label": "Sonora - Sinaloa Pacific Margin",
        "political_division": "Sonora, Sinaloa, Nayarit",
        "latitude": 26.5,
        "longitude": -109.8,
        "tectonic_layer": "Northwest Pacific margin",
    },
    {
        "label": "Jalisco - Colima",
        "political_division": "Jalisco, Colima",
        "latitude": 19.4,
        "longitude": -104.3,
        "tectonic_layer": "Rivera interaction corridor",
    },
    {
        "label": "Michoacán",
        "political_division": "Michoacán",
        "latitude": 18.8,
        "longitude": -101.7,
        "tectonic_layer": "Middle America Trench subduction corridor",
    },
    {
        "label": "Guerrero",
        "political_division": "Guerrero",
        "latitude": 17.6,
        "longitude": -99.7,
        "tectonic_layer": "Middle America Trench subduction corridor",
    },
    {
        "label": "Oaxaca",
        "political_division": "Oaxaca",
        "latitude": 16.7,
        "longitude": -96.6,
        "tectonic_layer": "Middle America Trench subduction corridor",
    },
    {
        "label": "Chiapas",
        "political_division": "Chiapas",
        "latitude": 15.8,
        "longitude": -93.3,
        "tectonic_layer": "Middle America Trench subduction corridor",
    },
    {
        "label": "Central Mexico",
        "political_division": "Ciudad de México, Estado de México, Morelos, Puebla",
        "latitude": 19.4,
        "longitude": -99.1,
        "tectonic_layer": "Inland interaction and crustal stress transfer",
    },
    {
        "label": "Veracruz - Gulf Coast",
        "political_division": "Veracruz, Tabasco",
        "latitude": 19.2,
        "longitude": -96.4,
        "tectonic_layer": "Gulf-side inland influence",
    },
    {
        "label": "Yucatán Peninsula",
        "political_division": "Yucatán, Campeche, Quintana Roo",
        "latitude": 20.7,
        "longitude": -89.0,
        "tectonic_layer": "Low-activity stable platform reference",
    },
]

REGION_CODE_FALLBACKS: dict[str, dict[str, str]] = {
    "MX_NORTH": {
        "label": "Northern Mexico Activity Band",
        "political_division": "Baja California, Sonora, Chihuahua, Coahuila",
        "tectonic_layer": "Northern prototype seismic aggregation",
    },
    "MX_CENTRAL": {
        "label": "Central Mexico Activity Band",
        "political_division": "Jalisco, Colima, Michoacán, Estado de México, Ciudad de México, Puebla",
        "tectonic_layer": "Central prototype seismic aggregation",
    },
    "MX_SOUTH": {
        "label": "Southern Mexico Activity Band",
        "political_division": "Guerrero, Oaxaca, Chiapas",
        "tectonic_layer": "Southern prototype seismic aggregation",
    },
}

DEFAULT_GEO = {
    "reference_geography": "Mexico prototype aggregation",
    "political_division": "Mexico",
    "tectonic_layer": "Prototype national seismic aggregation",
}


def _read_json_file(path: str | None) -> dict | None:
    if not path:
        return None
    candidate = Path(path)
    if not candidate.exists():
        return None
    return json.loads(candidate.read_text(encoding="utf-8"))





def _repo_root() -> Path:
    return Path(get_settings().repo_root)


def _reports_dir() -> Path:
    return _repo_root() / "artifacts" / "reports"


def _metrics_fallback() -> dict | None:
    candidate = _reports_dir() / "metrics.json"
    return _read_json_file(str(candidate)) if candidate.exists() else None

def _resolve_db_path(db_path: str | None = None) -> Path:
    settings = get_settings()
    return Path(create_schema(db_path or str(settings.db_path)))


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def _select_expr(columns: set[str], name: str, fallback_sql: str = "NULL") -> str:
    return name if name in columns else fallback_sql


def _cutoff_iso(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _distance_score(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)


def _fallback_from_region_code(region_code: str | None) -> dict[str, str]:
    if not region_code:
        return DEFAULT_GEO.copy()

    if region_code in REGION_CODE_FALLBACKS:
        payload = REGION_CODE_FALLBACKS[region_code]
        return {
            "reference_geography": payload["label"],
            "political_division": payload["political_division"],
            "tectonic_layer": payload["tectonic_layer"],
        }

    normalized = region_code.replace("_", " ").replace("-", " ").strip()
    titled = " ".join(token.capitalize() for token in normalized.split()) if normalized else "Mexico prototype aggregation"
    return {
        "reference_geography": titled,
        "political_division": "Prototype regional aggregation in Mexico",
        "tectonic_layer": "Prototype regional seismic layer",
    }


def _reference_geography(latitude: float | None, longitude: float | None, region_code: str | None = None) -> dict[str, str]:
    if latitude is not None and longitude is not None:
        nearest = min(
            REFERENCE_GEOGRAPHIES,
            key=lambda item: _distance_score(latitude, longitude, item["latitude"], item["longitude"]),
        )
        return {
            "reference_geography": nearest["label"],
            "political_division": nearest["political_division"],
            "tectonic_layer": nearest["tectonic_layer"],
        }

    return _fallback_from_region_code(region_code)


def _sanitize_geo_fields(payload: dict[str, Any]) -> dict[str, Any]:
    payload["reference_geography"] = payload.get("reference_geography") or DEFAULT_GEO["reference_geography"]
    payload["political_division"] = payload.get("political_division") or DEFAULT_GEO["political_division"]
    payload["tectonic_layer"] = payload.get("tectonic_layer") or DEFAULT_GEO["tectonic_layer"]
    return payload


def get_latest_summary(db_path: str | None = None) -> dict[str, object]:
    resolved_db_path = _resolve_db_path(db_path)
    with managed_connection(resolved_db_path) as connection:
        feature_generation = None
        if _table_exists(connection, "feature_generations"):
            feature_columns = _table_columns(connection, "feature_generations")
            feature_generation = connection.execute(
                f"""
                SELECT
                    {_select_expr(feature_columns, "generation_id", "feature_generation_id")} AS generation_id,
                    {_select_expr(feature_columns, "feature_set_version")} AS feature_set_version,
                    {_select_expr(feature_columns, "source_batch_id", "source_batch_scope")} AS source_batch_id,
                    {_select_expr(feature_columns, "status")} AS status,
                    {_select_expr(feature_columns, "created_at_utc", "completed_at_utc")} AS created_at_utc,
                    {_select_expr(feature_columns, "notes")} AS notes,
                    {_select_expr(feature_columns, "window_spec")} AS window_spec
                FROM feature_generations
                ORDER BY COALESCE(completed_at_utc, created_at_utc, started_at_utc) DESC, generation_id DESC
                LIMIT 1
                """
            ).fetchone()

        latest_model_run = None
        if _table_exists(connection, "model_runs"):
            model_columns = _table_columns(connection, "model_runs")
            latest_model_run = connection.execute(
                f"""
                SELECT
                    {_select_expr(model_columns, "run_id", "model_run_id")} AS run_id,
                    {_select_expr(model_columns, "feature_generation_id")} AS feature_generation_id,
                    {_select_expr(model_columns, "model_family", "model_name")} AS model_family,
                    {_select_expr(model_columns, "split_policy")} AS split_policy,
                    {_select_expr(model_columns, "train_row_count")} AS train_row_count,
                    {_select_expr(model_columns, "test_row_count")} AS test_row_count,
                    COALESCE({_select_expr(model_columns, "model_artifact_path")}, {_select_expr(model_columns, "artifact_path")}) AS model_artifact_path,
                    {_select_expr(model_columns, "status")} AS status,
                    COALESCE(
                        {_select_expr(model_columns, "completed_at_utc")},
                        {_select_expr(model_columns, "train_end_utc")},
                        {_select_expr(model_columns, "started_at_utc")},
                        {_select_expr(model_columns, "train_start_utc")}
                    ) AS completed_at_utc
                FROM model_runs
                ORDER BY COALESCE(completed_at_utc, train_end_utc, started_at_utc, train_start_utc) DESC, run_id DESC
                LIMIT 1
                """
            ).fetchone()

        latest_evaluation = None
        if _table_exists(connection, "evaluation_reports"):
            eval_columns = _table_columns(connection, "evaluation_reports")
            latest_evaluation = connection.execute(
                f"""
                SELECT
                    {_select_expr(eval_columns, "evaluation_id", "evaluation_report_id")} AS evaluation_id,
                    COALESCE({_select_expr(eval_columns, "model_run_id")}, {_select_expr(eval_columns, "run_id")}) AS model_run_id,
                    COALESCE({_select_expr(eval_columns, "report_json_path")}, {_select_expr(eval_columns, "metrics_json_path")}) AS report_json_path,
                    {_select_expr(eval_columns, "report_md_path")} AS report_md_path,
                    {_select_expr(eval_columns, "roc_plot_path")} AS roc_plot_path,
                    {_select_expr(eval_columns, "pr_plot_path")} AS pr_plot_path,
                    {_select_expr(eval_columns, "prob_hist_path")} AS prob_hist_path,
                    {_select_expr(eval_columns, "created_at_utc")} AS created_at_utc
                FROM evaluation_reports
                ORDER BY created_at_utc DESC, evaluation_id DESC
                LIMIT 1
                """
            ).fetchone()

    metrics_fallback = _metrics_fallback()
    if latest_model_run is None and metrics_fallback:
        latest_model_run = {
            "run_id": "baseline_publication_limited",
            "feature_generation_id": None if feature_generation is None else dict(feature_generation).get("generation_id"),
            "model_family": metrics_fallback.get("model_name", "baseline_random_forest"),
            "split_policy": metrics_fallback.get("split_policy") or "historical_holdout",
            "train_row_count": metrics_fallback.get("train_rows"),
            "test_row_count": metrics_fallback.get("test_rows"),
            "model_artifact_path": metrics_fallback.get("model_artifact_path") or "artifacts/models/baseline_model.joblib",
            "status": "publication-limited baseline",
            "completed_at_utc": None,
        }
    else:
        latest_model_run = None if latest_model_run is None else dict(latest_model_run)

    if latest_evaluation is None and metrics_fallback:
        latest_evaluation = {
            "evaluation_id": "publication_limited_baseline",
            "model_run_id": (latest_model_run or {}).get("run_id"),
            "report_json_path": str(_reports_dir() / "metrics.json"),
            "report_md_path": str(_reports_dir() / "evaluation_summary.md"),
            "roc_plot_path": str(_repo_root() / "artifacts" / "plots" / "eval_db0691981931ac9004df_roc.png"),
            "pr_plot_path": str(_repo_root() / "artifacts" / "plots" / "eval_db0691981931ac9004df_pr.png"),
            "prob_hist_path": str(_repo_root() / "artifacts" / "plots" / "eval_db0691981931ac9004df_probability_hist.png"),
        }
    else:
        latest_evaluation = None if latest_evaluation is None else dict(latest_evaluation)

    return {
        "latest_feature_generation": None if feature_generation is None else dict(feature_generation),
        "latest_model_run": latest_model_run,
        "latest_evaluation": latest_evaluation,
    }


def get_latest_region(region_code: str, db_path: str | None = None) -> dict[str, object] | None:
    resolved_db_path = _resolve_db_path(db_path)
    with managed_connection(resolved_db_path) as connection:
        if not _table_exists(connection, "region_features"):
            return None

        columns = _table_columns(connection, "region_features")
        region_name_expr = _select_expr(columns, "region_name", "region_code")
        target_label_expr = "COALESCE(target_label, target_risk_label)" if "target_risk_label" in columns else _select_expr(columns, "target_label")
        target_risk_score_expr = _select_expr(columns, "target_risk_score", "NULL")
        recent_rate_7d_expr = _select_expr(columns, "recent_rate_7d", "NULL")
        recent_rate_30d_expr = _select_expr(columns, "recent_rate_30d", "NULL")
        rolling_delta_rate_expr = _select_expr(columns, "rolling_delta_rate", "NULL")

        row = connection.execute(
            f"""
            SELECT
                COALESCE(region_code, {region_name_expr}) AS region_code,
                {region_name_expr} AS region_name,
                {_select_expr(columns, "window_start_utc")} AS window_start_utc,
                {_select_expr(columns, "window_end_utc")} AS window_end_utc,
                {_select_expr(columns, "event_count")} AS event_count,
                {_select_expr(columns, "mean_magnitude")} AS mean_magnitude,
                {_select_expr(columns, "max_magnitude")} AS max_magnitude,
                {_select_expr(columns, "mean_depth_km")} AS mean_depth_km,
                {_select_expr(columns, "latitude", "NULL")} AS latitude,
                {_select_expr(columns, "longitude", "NULL")} AS longitude,
                {recent_rate_7d_expr} AS recent_rate_7d,
                {recent_rate_30d_expr} AS recent_rate_30d,
                {rolling_delta_rate_expr} AS rolling_delta_rate,
                COALESCE({_select_expr(columns, "days_since_last_event", "9999.0")}, 9999.0) AS days_since_last_event,
                {target_label_expr} AS target_label,
                {target_risk_score_expr} AS target_risk_score
            FROM region_features
            WHERE COALESCE(region_code, {region_name_expr}) = ?
            ORDER BY COALESCE(window_end_utc, created_at_utc) DESC
            LIMIT 1
            """,
            (region_code,),
        ).fetchone()
    if row is None:
        return None
    payload = dict(row)
    payload.update(_reference_geography(payload.get("latitude"), payload.get("longitude"), payload.get("region_code")))
    return _sanitize_geo_fields(payload)




def get_latest_evaluation(db_path: str | None = None) -> dict[str, object]:
    resolved_db_path = _resolve_db_path(db_path)
    with managed_connection(resolved_db_path) as connection:
        if _table_exists(connection, "evaluation_reports"):
            columns = _table_columns(connection, "evaluation_reports")
            row = connection.execute(
                f"""
                SELECT
                    {_select_expr(columns, "evaluation_id", "evaluation_report_id")} AS evaluation_id,
                    COALESCE({_select_expr(columns, "model_run_id")}, {_select_expr(columns, "run_id")}) AS model_run_id,
                    COALESCE({_select_expr(columns, "report_json_path")}, {_select_expr(columns, "metrics_json_path")}) AS report_json_path,
                    {_select_expr(columns, "report_md_path")} AS report_md_path,
                    {_select_expr(columns, "roc_plot_path")} AS roc_plot_path,
                    {_select_expr(columns, "pr_plot_path")} AS pr_plot_path,
                    {_select_expr(columns, "prob_hist_path")} AS prob_hist_path
                FROM evaluation_reports
                ORDER BY COALESCE(created_at_utc, evaluation_id) DESC
                LIMIT 1
                """
            ).fetchone()
        else:
            row = None

    if row is not None:
        payload = dict(row)
        report_payload = _read_json_file(payload["report_json_path"])
        return {
            "evaluation_report_id": payload["evaluation_id"],
            "model_run_id": payload["model_run_id"],
            "metrics": None if report_payload is None else report_payload.get("metrics"),
            "report_json_path": payload["report_json_path"],
            "report_md_path": payload["report_md_path"],
            "roc_plot_path": payload["roc_plot_path"],
            "pr_plot_path": payload["pr_plot_path"],
            "prob_hist_path": payload["prob_hist_path"],
        }

    metrics_fallback = _metrics_fallback()
    if not metrics_fallback:
        return {
            "evaluation_report_id": None,
            "model_run_id": None,
            "metrics": None,
            "report_json_path": None,
            "report_md_path": None,
            "roc_plot_path": None,
            "pr_plot_path": None,
            "prob_hist_path": None,
        }

    return {
        "evaluation_report_id": "publication_limited_baseline",
        "model_run_id": "baseline_publication_limited",
        "metrics": metrics_fallback,
        "report_json_path": str(_reports_dir() / "metrics.json"),
        "report_md_path": str(_reports_dir() / "evaluation_summary.md"),
        "roc_plot_path": str(_repo_root() / "artifacts" / "plots" / "eval_db0691981931ac9004df_roc.png"),
        "pr_plot_path": str(_repo_root() / "artifacts" / "plots" / "eval_db0691981931ac9004df_pr.png"),
        "prob_hist_path": str(_repo_root() / "artifacts" / "plots" / "eval_db0691981931ac9004df_probability_hist.png"),
    }


def get_executive_mexico_map(db_path: str | None = None) -> dict[str, Any]:
    resolved_db_path = _resolve_db_path(db_path)
    cutoff_365 = _cutoff_iso(365)
    cutoff_30 = _cutoff_iso(30)

    with managed_connection(resolved_db_path) as connection:
        overview = connection.execute(
            """
            SELECT
                COUNT(*) AS total_events,
                MIN(occurred_at_utc) AS first_event_at_utc,
                MAX(occurred_at_utc) AS latest_event_at_utc,
                MAX(magnitude_value) AS strongest_magnitude
            FROM curated_events
            """
        ).fetchone()

        strongest_event = connection.execute(
            """
            SELECT occurred_at_utc, latitude, longitude, magnitude_value, depth_km, region_code
            FROM curated_events
            ORDER BY magnitude_value DESC, occurred_at_utc DESC
            LIMIT 1
            """
        ).fetchone()

        region_rows = connection.execute(
            """
            SELECT
                region_code,
                AVG(latitude) AS centroid_latitude,
                AVG(longitude) AS centroid_longitude,
                COUNT(*) AS event_count_total,
                SUM(CASE WHEN occurred_at_utc >= ? THEN 1 ELSE 0 END) AS event_count_last_365d,
                SUM(CASE WHEN occurred_at_utc >= ? THEN 1 ELSE 0 END) AS event_count_last_30d,
                MAX(magnitude_value) AS max_magnitude,
                AVG(magnitude_value) AS mean_magnitude,
                AVG(depth_km) AS mean_depth_km
            FROM curated_events
            GROUP BY region_code
            ORDER BY event_count_total DESC
            """,
            (cutoff_365, cutoff_30),
        ).fetchall()

        notable_events = connection.execute(
            """
            SELECT occurred_at_utc, latitude, longitude, magnitude_value, depth_km, region_code
            FROM curated_events
            WHERE magnitude_value >= 7.0
            ORDER BY magnitude_value DESC, occurred_at_utc DESC
            LIMIT 12
            """
        ).fetchall()

        recent_significant = connection.execute(
            """
            SELECT occurred_at_utc, latitude, longitude, magnitude_value, depth_km, region_code
            FROM curated_events
            WHERE occurred_at_utc >= ? AND magnitude_value >= 4.0
            ORDER BY occurred_at_utc DESC, magnitude_value DESC
            LIMIT 25
            """,
            (cutoff_365,),
        ).fetchall()

    region_payload = [dict(row) for row in region_rows]
    max_event_count = max([row.get("event_count_total") or 0 for row in region_payload] or [1])
    max_recent_365 = max([row.get("event_count_last_365d") or 0 for row in region_payload] or [1])
    max_magnitude = max([row.get("max_magnitude") or 0 for row in region_payload] or [1])

    enriched_regions: list[dict[str, Any]] = []
    for row in region_payload:
        count_norm = (row.get("event_count_total") or 0) / max_event_count if max_event_count else 0
        recent_norm = (row.get("event_count_last_365d") or 0) / max_recent_365 if max_recent_365 else 0
        mag_norm = (row.get("max_magnitude") or 0) / max_magnitude if max_magnitude else 0
        executive_risk_index = round((0.45 * count_norm + 0.25 * recent_norm + 0.30 * mag_norm) * 100, 2)

        if executive_risk_index >= 66:
            risk_band = "High"
            light_color = [255, 82, 82, 220]
            dark_color = [255, 110, 110, 220]
        elif executive_risk_index >= 40:
            risk_band = "Moderate"
            light_color = [255, 193, 7, 220]
            dark_color = [255, 214, 10, 220]
        else:
            risk_band = "Baseline"
            light_color = [0, 188, 212, 220]
            dark_color = [77, 208, 225, 220]

        geography = _reference_geography(row.get("centroid_latitude"), row.get("centroid_longitude"), row.get("region_code"))
        enriched = {
            **row,
            **geography,
            "label": geography["reference_geography"],
            "executive_risk_index": executive_risk_index,
            "risk_band": risk_band,
            "light_color": light_color,
            "dark_color": dark_color,
            "radius": max(25000, int(((row.get("event_count_total") or 1) / max_event_count) * 120000)),
        }
        enriched_regions.append(_sanitize_geo_fields(enriched))

    top_affected_zones = sorted(
        enriched_regions,
        key=lambda r: (-(r.get("event_count_total") or 0), -(r.get("max_magnitude") or 0)),
    )[:5]

    enriched_notable_events = []
    for row in [dict(row) for row in notable_events]:
        row.update(_reference_geography(row.get("latitude"), row.get("longitude"), row.get("region_code")))
        enriched_notable_events.append(_sanitize_geo_fields(row))

    enriched_recent_events = []
    for row in [dict(row) for row in recent_significant]:
        row.update(_reference_geography(row.get("latitude"), row.get("longitude"), row.get("region_code")))
        enriched_recent_events.append(_sanitize_geo_fields(row))

    strongest_payload = None if strongest_event is None else dict(strongest_event)
    if strongest_payload is not None:
        strongest_payload.update(
            _reference_geography(strongest_payload.get("latitude"), strongest_payload.get("longitude"), strongest_payload.get("region_code"))
        )
        strongest_payload = _sanitize_geo_fields(strongest_payload)

    tectonic_context = [
        {
            "zone": row.get("region_code"),
            "label": row.get("reference_geography"),
            "political_division": row.get("political_division"),
            "tectonic_layer": row.get("tectonic_layer"),
            "risk_band": row.get("risk_band"),
            "executive_risk_index": row.get("executive_risk_index"),
            "event_count_total": row.get("event_count_total"),
            "max_magnitude": row.get("max_magnitude"),
            "context_note": "Prototype activity layer derived from historical event concentration and magnitude. Not an official tectonic boundary layer.",
        }
        for row in sorted(
            enriched_regions,
            key=lambda r: (-(r.get("executive_risk_index") or 0), -(r.get("event_count_total") or 0)),
        )
    ]

    return {
        "overview": None if overview is None else dict(overview),
        "strongest_event": strongest_payload,
        "regions": enriched_regions,
        "top_affected_zones": top_affected_zones,
        "notable_events": enriched_notable_events,
        "recent_significant_events": enriched_recent_events,
        "tectonic_context": tectonic_context,
        "method_note": "Executive risk index is a prototype ranking derived from event density, recent activity, and strongest historical magnitude within each prototype region.",
        "map_note": "Map layers reflect prototype region aggregations and selected historical event highlights from curated data. Geographic labels are approximate reference areas derived from event coordinates or region-code fallback, not official geocoding.",
    }
