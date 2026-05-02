from __future__ import annotations

import json
from pathlib import Path

from src.api.repository import (
    get_executive_mexico_map,
    get_latest_evaluation,
    get_latest_region,
    get_latest_summary,
)
from src.common.settings import get_settings
from src.common.sqlite import managed_connection

PUBLIC_SQLITE_DISPLAY_PATH = "PSRP/artifacts/sqlite/seismic_prototype.db"

HERO_PLOT_FILENAMES = [
    "metrics_panel.png",
    "pipeline_trace.png",
    "probabilistic_risk_map.png",
    "risk_heatmap.png",
    "regional_event_counts.png",
    "magnitude_distribution.png",
    "model_summary_panel.png",
    "methodology_traceability_cycle.png",
]
HERO_REPORT_FILENAMES = [
    "demo_evidence.md",
    "evaluation_summary.md",
    "class_balance_audit.md",
]

def _repo_root() -> Path:
    return get_settings().repo_root

def _artifacts_dir() -> Path:
    return get_settings().artifacts_dir

def _resolve_path(path_like: str | Path | None) -> Path | None:
    if not path_like:
        return None
    path = Path(path_like)
    if path.is_absolute():
        return path if path.exists() else None
    candidate = _repo_root() / path
    return candidate if candidate.exists() else None

def _display_path(path_like: str | Path | None) -> str:
    """Return a publication-safe relative path for UI display only."""
    if not path_like:
        return ""
    try:
        path = Path(path_like)
        root = _repo_root()
        if path.is_absolute():
            return str(path.relative_to(root)).replace("\\", "/")
        return str(path).replace("\\", "/")
    except Exception:
        return Path(str(path_like)).name

def _read_text_file(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")

def _read_json_file(path: Path | None) -> dict[str, object] | None:
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))

def fetch_summary(db_path: str | None = None) -> dict[str, object]:
    return get_latest_summary(db_path)

def fetch_region_codes(db_path: str | None = None) -> list[str]:
    settings = get_settings()
    with managed_connection(db_path or settings.sqlite_path) as connection:
        rows = connection.execute(
            "SELECT DISTINCT COALESCE(region_code, region_name) AS region_code FROM region_features ORDER BY region_code ASC"
        ).fetchall()
    return [row["region_code"] for row in rows]

def fetch_region_latest(region_code: str, db_path: str | None = None) -> dict[str, object] | None:
    return get_latest_region(region_code, db_path)

def fetch_evaluation(db_path: str | None = None) -> dict[str, object]:
    return get_latest_evaluation(db_path)

def fetch_executive_mexico_map_payload(db_path: str | None = None) -> dict[str, object]:
    return get_executive_mexico_map(db_path)

def fetch_publication_snapshot() -> dict[str, object]:
    reports_dir = _artifacts_dir() / "reports"
    candidates = sorted(reports_dir.glob("publication_data_snapshot_*.json"))
    if not candidates:
        return {}
    return _read_json_file(candidates[-1]) or {}

def fetch_hero_plots() -> list[dict[str, str]]:
    plots_dir = _artifacts_dir() / "plots"
    results: list[dict[str, str]] = []
    for filename in HERO_PLOT_FILENAMES:
        svg_path = plots_dir / filename.replace('.png', '.svg')
        png_path = plots_dir / filename
        path = svg_path if svg_path.exists() else png_path
        if path.exists():
            results.append({"title": filename.replace(".png", "").replace("_", " ").title(), "path": str(path)})
    return results

def fetch_evaluation_plots(db_path: str | None = None) -> list[dict[str, str]]:
    evaluation = fetch_evaluation(db_path)
    candidates = [
        ("ROC Curve", evaluation.get("roc_plot_path")),
        ("Precision-Recall Curve", evaluation.get("pr_plot_path")),
        ("Probability Histogram", evaluation.get("prob_hist_path")),
    ]
    results: list[dict[str, str]] = []
    for title, path_like in candidates:
        resolved = _resolve_path(path_like)
        if resolved is not None:
            svg_candidate = resolved.with_suffix('.svg')
            chosen = svg_candidate if svg_candidate.exists() else resolved
            results.append({"title": title, "path": str(chosen)})
    return results

def fetch_hero_reports() -> list[dict[str, str]]:
    reports_dir = _artifacts_dir() / "reports"
    results: list[dict[str, str]] = []
    for filename in HERO_REPORT_FILENAMES:
        path = reports_dir / filename
        if path.exists():
            content = _read_text_file(path)
            results.append({
                "title": filename.replace(".md", "").replace("_", " ").title(),
                "path": str(path),
                "content": content or "",
            })
    return results

def fetch_publication_bundle(db_path: str | None = None) -> dict[str, object]:
    return {
        "summary": fetch_summary(db_path),
        "evaluation": fetch_evaluation(db_path),
        "executive_mexico_map": fetch_executive_mexico_map_payload(db_path),
        "publication_snapshot": fetch_publication_snapshot(),
        "region_codes": fetch_region_codes(db_path),
        "hero_plots": fetch_hero_plots(),
        "evaluation_plots": fetch_evaluation_plots(db_path),
        "hero_reports": fetch_hero_reports(),
        "sqlite_path": PUBLIC_SQLITE_DISPLAY_PATH,
        "sqlite_path_display": PUBLIC_SQLITE_DISPLAY_PATH,
    }
