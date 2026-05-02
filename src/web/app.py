from __future__ import annotations

import calendar
import html
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

from src.web.repository import (
    fetch_evaluation,
    fetch_evaluation_plots,
    fetch_executive_mexico_map_payload,
    fetch_hero_plots,
    fetch_hero_reports,
    fetch_publication_bundle,
    fetch_publication_snapshot,
    fetch_region_codes,
    fetch_region_latest,
    fetch_summary,
)

PLOT_PURPOSES = {
    "pipeline_trace.png": ("Prototype workflow traceability", "Trazabilidad del flujo del prototipo"),
    "metrics_panel.png": ("Executive summary of persisted indicators", "Resumen ejecutivo de indicadores persistidos"),
    "probabilistic_risk_map.png": ("Prototype regional concentration ranking", "Ranking de concentración regional del prototipo"),
    "risk_heatmap.png": ("Relative concentration heatmap", "Mapa de calor de concentración relativa"),
    "regional_event_counts.png": ("Historical event concentration comparison", "Comparación de concentración histórica de eventos"),
    "magnitude_distribution.png": ("Observed magnitude distribution", "Distribución observada de magnitudes"),
    "model_summary_panel.png": ("Current model and publication posture", "Estado actual del modelo y de la publicación"),
    "methodology_traceability_cycle.png": ("Ingestion and treatment traceability cycle", "Ciclo de trazabilidad de ingesta y tratamiento"),
}

REPORT_SUMMARIES = {
    "Demo Evidence": (
        "Explains how the current publication surface is supported by persisted evidence artifacts and why the pipeline trace matters for auditability.",
        "Explica cómo la superficie actual de publicación está respaldada por artefactos persistidos de evidencia y por qué el pipeline trace es importante para la auditabilidad.",
    ),
    "Evaluation Summary": (
        "Connects the current evaluation posture with model intent, publication limits, and the discipline of not fabricating unavailable evidence.",
        "Conecta la postura actual de evaluación con la intención del modelo, los límites de publicación y la disciplina de no fabricar evidencia no disponible.",
    ),
    "Predemo Status": (
        "Summarizes operational readiness from a publication perspective, emphasizing what the audience may safely infer and what remains bounded by prototype scope.",
        "Resume la preparación operativa desde la perspectiva de publicación, enfatizando qué puede inferir el público de forma segura y qué permanece acotado por el alcance del prototipo.",
    ),
    "Class Balance Audit": (
        "Contextualizes how data distribution affects interpretability, concentration patterns, and the limits of public probabilistic communication.",
        "Contextualiza cómo la distribución de datos afecta la interpretabilidad, los patrones de concentración y los límites de la comunicación probabilística pública.",
    ),
}

REPORT_PLOT_MAP = {
    "Demo Evidence": "pipeline_trace.png",
    "Evaluation Summary": "model_summary_panel.png",
    "Predemo Status": "metrics_panel.png",
    "Class Balance Audit": "magnitude_distribution.png",
}

FUTURE_STEPS = [
    (
        "On-premise AI services",
        "Deploy local inference or feature-ranking services near the SQLite authority to support low-latency experimentation with bounded MLOps.",
        "Servicios de IA on-premise",
        "Desplegar servicios locales de inferencia o priorización de features cerca de la autoridad SQLite para soportar experimentación de baja latencia con MLOps acotado.",
    ),
    (
        "Cloud augmentation",
        "Add optional cloud pipelines for heavier training, archival replication, or federation without making the prototype cloud-dependent.",
        "Expansión cloud",
        "Agregar pipelines opcionales en nube para entrenamiento más pesado, replicación archivística o federación sin volver el prototipo dependiente de cloud.",
    ),
    (
        "Canonical geometry ingestion",
        "Formally ingest political boundaries, tectonic geometries, and validated geospatial layers before presenting them as authoritative map overlays.",
        "Ingesta de geometría canónica",
        "Ingerir formalmente límites políticos, geometrías tectónicas y capas geoespaciales validadas antes de presentarlas como overlays autoritativos.",
    ),
    (
        "Expanded ML stages",
        "Introduce richer modeling stages such as calibration, uncertainty monitoring, temporal drift checks, and scenario analysis under explicit governance gates.",
        "Etapas ampliadas de ML",
        "Introducir etapas de modelado más ricas como calibración, monitoreo de incertidumbre, revisión de drift temporal y análisis de escenarios bajo compuertas explícitas de gobernanza.",
    ),
]

def tr(en: str, es: str) -> str:
    return es if st.session_state.get("lang", "en") == "es" else en

def inject_styles() -> None:
    st.markdown(
        """
<style>
html, body, [class*="css"] { font-size: 17px; }
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(160,160,160,0.20);
    padding: 1rem 0.9rem 0.8rem 0.9rem;
    border-radius: 16px;
}
div[data-testid="stMetricLabel"] { font-size: 1rem; font-weight: 650; }
div[data-testid="stMetricValue"] { font-size: 1.54rem; font-weight: 780; }
.stMarkdown p, .stCaption, .stText { font-size: 1.04rem; line-height: 1.62; }
h1, h2, h3 { letter-spacing: 0.2px; }
.interpretation-box {
    border-left: 6px solid #d97706;
    background: rgba(217, 119, 6, 0.14);
    padding: 1rem 1rem;
    border-radius: 12px;
    margin-top: 0.5rem;
}
.findings-box {
    border-left: 6px solid #60a5fa;
    background: rgba(96,165,250,0.10);
    padding: 0.95rem 1rem;
    border-radius: 12px;
    margin-bottom: 0.7rem;
}
.demonstrates-box {
    border-left: 6px solid #3b82f6;
    background: rgba(59,130,246,0.14);
    padding: 1rem 1rem;
    border-radius: 16px;
    margin-bottom: 0.9rem;
}
.narrative-box {
    border-left: 6px solid #34d399;
    background: rgba(52,211,153,0.08);
    padding: 0.95rem 1rem;
    border-radius: 12px;
    margin-bottom: 0.8rem;
}
.warning-box {
    border-left: 6px solid #ef4444;
    background: rgba(239,68,68,0.08);
    padding: 0.95rem 1rem;
    border-radius: 12px;
    margin-bottom: 0.8rem;
}
.hero-box {
    border: 1px solid rgba(160,160,160,0.18);
    background: rgba(255,255,255,0.03);
    padding: 1rem 1rem;
    border-radius: 16px;
    margin-bottom: 0.9rem;
}
section[data-testid="stSidebar"] code { white-space: pre-wrap; }
.path-box {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(160,160,160,0.18);
    border-radius: 12px;
    padding: 0.8rem 0.9rem;
    font-size: 0.92rem;
    line-height: 1.45;
    word-break: break-word;
    margin-bottom: 0.65rem;
}
.path-box .subtle + .subtle { display:block; margin-top: 0.25rem; color:#94a3b8; font-size:0.84rem; }
.authority-meta {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(160,160,160,0.12);
    border-radius: 12px;
    padding: 0.85rem 0.9rem;
    margin-bottom: 0.65rem;
}
.authority-meta b { display:block; font-size: 0.92rem; margin-bottom: 0.2rem; }
.authority-meta .subtle { color:#cbd5e1; font-size:0.88rem; }
.table-wrap { overflow-x:auto; margin-bottom:0.4rem; }
.compact-table { width:100%; border-collapse:collapse; font-size:0.95rem; }
.compact-table th, .compact-table td { border:1px solid rgba(148,163,184,0.18); padding:0.55rem 0.6rem; vertical-align:top; }
.compact-table th { background:rgba(255,255,255,0.04); text-align:left; }
.wrap-value { max-width: 420px; white-space: normal; overflow-wrap:anywhere; }
.endpoint-chip { display:inline-block; padding:0.38rem 0.65rem; margin:0.15rem 0.35rem 0.15rem 0; border-radius:999px; background:rgba(96,165,250,0.12); border:1px solid rgba(96,165,250,0.24); font-size:0.92rem; }
.section-jump { color:#cbd5e1; font-size:0.95rem; margin-top:0.35rem; }

.metric-card {
    min-height: 112px;
    background: linear-gradient(180deg, rgba(15,23,42,0.72), rgba(15,23,42,0.46));
    border: 1px solid rgba(148,163,184,0.20);
    border-radius: 18px;
    padding: 0.95rem 1rem;
    margin-bottom: 0.72rem;
    box-shadow: 0 10px 26px rgba(2,6,23,0.12);
}
.metric-label { color:#cbd5e1; font-size:0.88rem; font-weight:720; letter-spacing:.01em; margin-bottom:.48rem; }
.metric-value { color:#f8fafc; font-size:1.34rem; line-height:1.18; font-weight:820; overflow-wrap:anywhere; white-space:normal; }
.metric-note { color:#94a3b8; font-size:0.82rem; margin-top:.45rem; line-height:1.35; }
.surface-card {
    border: 1px solid rgba(148,163,184,.18);
    border-left-width: 7px;
    border-radius: 18px;
    padding: 1rem 1.05rem;
    margin-bottom: .85rem;
    background: rgba(15,23,42,.34);
    line-height: 1.58;
}
.surface-card b { font-size:1.02rem; }
.surface-blue { border-left-color:#3b82f6; background:rgba(59,130,246,.10); }
.surface-green { border-left-color:#34d399; background:rgba(52,211,153,.08); }
.surface-amber { border-left-color:#f59e0b; background:rgba(245,158,11,.10); }
.surface-red { border-left-color:#ef4444; background:rgba(239,68,68,.08); }
.badge { display:inline-block; padding:.32rem .62rem; border-radius:999px; border:1px solid rgba(148,163,184,.22); font-size:.82rem; font-weight:760; letter-spacing:.01em; line-height:1.2; margin:.1rem .15rem .1rem 0; }
.badge-blue { background:rgba(59,130,246,.12); color:#bfdbfe; border-color:rgba(59,130,246,.28); }
.badge-green { background:rgba(52,211,153,.10); color:#bbf7d0; border-color:rgba(52,211,153,.26); }
.badge-amber { background:rgba(245,158,11,.12); color:#fde68a; border-color:rgba(245,158,11,.30); }
.badge-muted { background:rgba(148,163,184,.10); color:#cbd5e1; border-color:rgba(148,163,184,.22); }
.map-detail { border-radius:18px; border:1px solid rgba(148,163,184,.18); padding:1rem; margin:.8rem 0 1rem; background:rgba(15,23,42,.28); }
.map-detail h4 { margin:.05rem 0 .75rem; font-size:1.04rem; }
.map-detail-grid { display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:.75rem; }
.map-detail-grid div { background:rgba(255,255,255,.035); border:1px solid rgba(148,163,184,.14); border-radius:14px; padding:.7rem .75rem; }
.map-detail-grid span { display:block; color:#94a3b8; font-size:.78rem; font-weight:700; margin-bottom:.3rem; }
.map-detail-grid b { color:#f8fafc; font-size:1rem; line-height:1.25; overflow-wrap:anywhere; }
@media (max-width: 900px){ .map-detail-grid { grid-template-columns:1fr 1fr; } }
@media (max-width: 640px){ .map-detail-grid { grid-template-columns:1fr; } }

</style>
        """,
        unsafe_allow_html=True,
    )

def _safe_metric_value(value: object, fallback: str = "Not published") -> str:
    if value is None:
        return fallback
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if abs(value) >= 100:
            return f"{value:,.2f}"
        return f"{value:.2f}"
    return str(value)


def _short_date(value: object) -> str:
    if not value:
        return "Not published"
    text = str(value)
    if "T" in text:
        return text.split("T", 1)[0]
    return text[:10] if len(text) >= 10 else text


def _display_state(value: object, fallback: str) -> str:
    if value in (None, "", "—"):
        return fallback
    return str(value)


def _publication_state(value: object, fallback: str | None = None) -> str:
    if value in (None, "", "—"):
        return fallback or tr("Not published in current release", "No publicado en la versión actual")
    if isinstance(value, str) and value.lower().replace("_", "-") in {"not published", "not-published", "publication limited", "publication-limited"}:
        return tr("Publication-limited", "Limitado para publicación")
    return _safe_metric_value(value)


def _normalize_authority_path(path_like: object) -> str:
    return "PSRP/artifacts/sqlite/seismic_prototype.db"


def _compact_authority_path(path_like: object) -> str:
    return "PSRP/artifacts/sqlite/seismic_prototype.db"


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _html_table(rows: list[dict[str, object]], headers: list[str] | None = None) -> str:
    if not rows:
        return ""
    headers = headers or list(rows[0].keys())
    thead = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    body_rows = []
    for row in rows:
        tds = []
        for h in headers:
            val = row.get(h, "")
            sval = _safe_metric_value(val, fallback=tr("Not published", "No publicado"))
            esc = _esc(sval)
            tds.append(f'<td class="wrap-value" title="{esc}">{esc}</td>')
        body_rows.append("<tr>" + "".join(tds) + "</tr>")
    return f'<div class="table-wrap"><table class="compact-table"><thead><tr>{thead}</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>'


def _metric_html(label: str, value: object, note: str | None = None) -> str:
    note_html = f'<div class="metric-note">{_esc(note)}</div>' if note else ""
    return (
        '<div class="metric-card">'
        f'<div class="metric-label">{_esc(label)}</div>'
        f'<div class="metric-value">{_esc(_safe_metric_value(value))}</div>'
        f'{note_html}'
        '</div>'
    )


def _present_metric(label: str, value: object, note: str | None = None) -> None:
    st.markdown(_metric_html(label, value, note), unsafe_allow_html=True)


def _badge(label: str, tone: str = "blue") -> str:
    return f'<span class="badge badge-{_esc(tone)}">{_esc(label)}</span>'


def _status_badge(value: object, fallback: str | None = None) -> str:
    text = _publication_state(value, fallback=fallback)
    normalized = str(text).lower()
    if "not" in normalized or "fuera" in normalized or "no publicado" in normalized:
        return _badge(text, "muted")
    if "limited" in normalized or "limitado" in normalized or "baseline" in normalized:
        return _badge(text, "amber")
    return _badge(text, "green")


def _surface_card(title: str, body: str, tone: str = "blue") -> str:
    return f'<div class="surface-card surface-{_esc(tone)}"><b>{_esc(title)}</b><br><br>{_esc(body)}</div>'


def _map_detail_panel(title: str, rows: list[tuple[str, object]], tone: str = "blue") -> str:
    items = "".join(f'<div><span>{_esc(label)}</span><b>{_esc(_safe_metric_value(value))}</b></div>' for label, value in rows)
    return f'<div class="map-detail map-detail-{_esc(tone)}"><h4>{_esc(title)}</h4><div class="map-detail-grid">{items}</div></div>'

def _top_item(items: list[dict], field: str) -> dict | None:
    if not items:
        return None
    return max(items, key=lambda item: item.get(field, 0) or 0)

def _month_label(value: object) -> str:
    try:
        month = int(str(value))
        if 1 <= month <= 12:
            return calendar.month_abbr[month]
    except Exception:
        pass
    return str(value)

def _monthly_df(rows: list[dict], value_key: str, value_label: str) -> pd.DataFrame:
    data = [{"Month": _month_label(row.get("month")), value_label: row.get(value_key, 0)} for row in rows]
    return pd.DataFrame(data).set_index("Month") if data else pd.DataFrame(columns=[value_label])

def _yearly_df(rows: list[dict], value_key: str, value_label: str) -> pd.DataFrame:
    data = [{"Year": str(row.get("year")), value_label: row.get(value_key, 0)} for row in rows]
    return pd.DataFrame(data).set_index("Year") if data else pd.DataFrame(columns=[value_label])

def _regional_df(rows: list[dict], value_key: str, value_label: str, limit: int = 8) -> pd.DataFrame:
    data = [{"Region": row.get("reference_geography", row.get("region_code", "—")), value_label: row.get(value_key, 0)} for row in rows[:limit]]
    return pd.DataFrame(data).set_index("Region") if data else pd.DataFrame(columns=[value_label])



def _short_region_label(value: object) -> str:
    raw = str(value or tr("Not published", "No publicado"))
    replacements = {
        "Baja California / Gulf of California": "Baja Calif. / Gulf",
        "Jalisco - Colima": "Jalisco-Colima",
        "Central Mexico Activity Band": "Central MX Band",
    }
    for old, new in replacements.items():
        raw = raw.replace(old, new)
    return raw if len(raw) <= 20 else raw[:17] + "…"

def _regional_chart_df(rows: list[dict], value_key: str, value_label: str, limit: int = 6) -> pd.DataFrame:
    data = []
    for row in rows[:limit]:
        label = row.get("reference_geography", row.get("region_code", "—"))
        data.append({"Region": _short_region_label(label), value_label: row.get(value_key, 0)})
    return pd.DataFrame(data).set_index("Region") if data else pd.DataFrame(columns=[value_label])

def _kv_rows(fields: list[tuple[str, object]]) -> list[dict[str, str]]:
    return [{"Field": label, "Value": _safe_metric_value(value)} for label, value in fields]

def _plot_lookup(hero_plots: list[dict]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for item in hero_plots:
        path = Path(item["path"])
        lookup[path.name] = item["path"]
        lookup[f"{path.stem}.png"] = item["path"]
        lookup[f"{path.stem}.svg"] = item["path"]
    return lookup

def _clean_rows(rows: list[dict]) -> list[dict]:
    return [{k: ("—" if v is None else v) for k, v in row.items()} for row in rows]

def _section_intro(title_en: str, title_es: str, body_en: str, body_es: str) -> None:
    st.markdown(f"### {tr(title_en, title_es)}")
    st.caption(tr(body_en, body_es))

def _region_meta(snapshot: dict[str, object]) -> dict[str, dict]:
    rows = snapshot.get("regional_concentration") or []
    return {row.get("region_code"): row for row in rows if row.get("region_code")}

def _friendly_region_label(code: str, meta: dict[str, dict]) -> str:
    row = meta.get(code) or {}
    if code.startswith("MX_"):
        ref = row.get("reference_geography") or code
        pol = row.get("political_division") or tr("Prototype band", "Banda del prototipo")
        return f"{ref} ({code}) — {pol}"
    if code.startswith("bin_"):
        coords = code.replace("bin_", "").replace("_", ", ")
        pol = row.get("political_division") or tr("Approximate grid cell", "Celda de cuadrícula aproximada")
        return f"{tr('Grid cell', 'Celda')} {coords} — {pol}"
    return f"{row.get('reference_geography', code)} ({code})"

def _artifact_rows(hero_plots: list[dict], hero_reports: list[dict]) -> tuple[list[dict], list[dict]]:
    plot_rows = []
    for item in hero_plots:
        filename = f"{Path(item['path']).stem}.png"
        role = PLOT_PURPOSES.get(filename, ("Publication visual support", "Soporte visual de publicación"))
        plot_rows.append({"Plot": item["title"], "Role": tr(role[0], role[1]), "Status": tr("Available", "Disponible")})
    report_rows = []
    for item in hero_reports:
        role = REPORT_SUMMARIES.get(item["title"], ("Publication narrative support.", "Soporte narrativo de publicación."))
        report_rows.append({"Report": item["title"], "Role": tr(role[0], role[1]), "Status": tr("Available", "Disponible")})
    return plot_rows, report_rows


def _display_or_na(value: object, fallback: str | None = None) -> str:
    if value in (None, "", "—"):
        return fallback or tr("Not published", "No publicado")
    return _safe_metric_value(value)


def _tooltip_record(
    title: object,
    line_1: object,
    line_2: object,
    line_3: object,
    line_4: object,
    line_5: object | None = None,
) -> dict[str, str]:
    return {
        "tooltip_title": _display_or_na(title),
        "tooltip_line_1": _display_or_na(line_1, tr("Political division: Not published", "División política: No publicada")),
        "tooltip_line_2": _display_or_na(line_2, tr("Layer: Prototype context", "Capa: Contexto del prototipo")),
        "tooltip_line_3": _display_or_na(line_3, tr("Risk band: Contextual", "Banda de riesgo: Contextual")),
        "tooltip_line_4": _display_or_na(line_4, tr("Executive risk index: Not applicable", "Índice ejecutivo de riesgo: No aplicable")),
        "tooltip_line_5": _display_or_na(line_5, tr("Magnitude / events: Not published", "Magnitud / eventos: No publicado")),
    }


def _normalize_region_map_records(rows: list[dict], color_key: str) -> list[dict]:
    normalized: list[dict] = []
    for item in rows:
        label = item.get("label") or item.get("reference_geography") or item.get("region_code")
        political = item.get("political_division") or item.get("reference_geography") or tr("Prototype region", "Región del prototipo")
        tectonic = item.get("tectonic_layer") or item.get("tectonic_context") or tr("Aggregated prototype region", "Región agregada del prototipo")
        risk_band = item.get("risk_band") or item.get("risk_level") or item.get("relative_risk_band") or tr("Descriptive concentration band", "Banda descriptiva de concentración")
        executive_index = item.get("executive_risk_index") or item.get("risk_index") or item.get("risk_score")
        total_events = item.get("event_count_total") or item.get("event_count") or item.get("total_events")
        max_magnitude = item.get("max_magnitude") or item.get("strongest_magnitude")
        tooltip = _tooltip_record(
            label,
            f"{tr('Political division', 'División política')}: {political}",
            f"{tr('Layer', 'Capa')}: {tectonic}",
            f"{tr('Risk band', 'Banda de riesgo')}: {risk_band}",
            f"{tr('Executive risk index', 'Índice ejecutivo de riesgo')}: {_display_or_na(executive_index, tr('Not published', 'No publicado'))}",
            f"{tr('Total events', 'Eventos totales')}: {_display_or_na(total_events)} · {tr('Max magnitude', 'Magnitud máxima')}: {_display_or_na(max_magnitude)}",
        )
        normalized.append({
            **item,
            **tooltip,
            "map_color": item.get(color_key) or item.get("light_color") or [96, 165, 250, 180],
            "safe_radius": item.get("radius") or 25000,
            "display_label": political,
        })
    return normalized


def _normalize_event_map_records(rows: list[dict], layer_name: str, fill_color: list[int]) -> list[dict]:
    normalized: list[dict] = []
    for item in rows:
        label = item.get("label") or item.get("reference_geography") or item.get("region_code") or tr("Recorded event", "Evento registrado")
        political = item.get("political_division") or item.get("reference_geography") or tr("Not published", "No publicado")
        magnitude = item.get("magnitude_value") or item.get("magnitude") or item.get("max_magnitude")
        event_time = item.get("event_time_utc") or item.get("occurred_at_utc") or item.get("date") or item.get("event_date")
        tooltip = _tooltip_record(
            label,
            f"{tr('Political division', 'División política')}: {political}",
            f"{tr('Layer', 'Capa')}: {layer_name}",
            f"{tr('Risk band', 'Banda de riesgo')}: {tr('Contextual event layer', 'Capa contextual de eventos')}",
            f"{tr('Executive risk index', 'Índice ejecutivo de riesgo')}: {tr('Not applicable', 'No aplicable')}",
            f"{tr('Magnitude', 'Magnitud')}: {_display_or_na(magnitude)} · {tr('Date', 'Fecha')}: {_short_date(event_time)}",
        )
        try:
            safe_radius = float(magnitude) if magnitude not in (None, "", "—") else 3.0
        except Exception:
            safe_radius = 3.0
        normalized.append({
            **item,
            **tooltip,
            "map_color": fill_color,
            "safe_radius": safe_radius,
        })
    return normalized


def _build_mexico_map(payload: dict[str, object], map_style: str, color_key: str, zoom_enabled: bool = False) -> pdk.Deck:
    regions = _normalize_region_map_records(payload.get("regions") or [], color_key)
    notable_events = _normalize_event_map_records(
        payload.get("notable_events") or [],
        tr("Notable historical event", "Evento histórico notable"),
        [255, 99, 71, 235],
    )
    recent_events = _normalize_event_map_records(
        payload.get("recent_significant_events") or [],
        tr("Recent significant event", "Evento significativo reciente"),
        [0, 255, 200, 180] if color_key == "dark_color" else [0, 140, 170, 190],
    )
    neutral = [255, 255, 255, 180] if color_key == "dark_color" else [40, 40, 40, 160]
    region_layer = pdk.Layer(
        "ScatterplotLayer",
        data=regions,
        get_position="[centroid_longitude, centroid_latitude]",
        get_fill_color="map_color",
        get_radius="safe_radius",
        radius_min_pixels=18,
        radius_max_pixels=72,
        stroked=True,
        get_line_color=neutral,
        line_width_min_pixels=1,
        pickable=True,
        opacity=0.72,
    )
    event_layer = pdk.Layer(
        "ScatterplotLayer",
        data=notable_events,
        get_position="[longitude, latitude]",
        get_fill_color="map_color",
        get_radius="safe_radius * 10000",
        radius_min_pixels=10,
        radius_max_pixels=34,
        stroked=True,
        get_line_color=neutral,
        line_width_min_pixels=1,
        pickable=True,
        opacity=0.92,
    )
    recent_layer = pdk.Layer(
        "ScatterplotLayer",
        data=recent_events,
        get_position="[longitude, latitude]",
        get_fill_color="map_color",
        get_radius="safe_radius * 6500",
        radius_min_pixels=6,
        radius_max_pixels=22,
        stroked=True,
        get_line_color=neutral,
        line_width_min_pixels=1,
        pickable=True,
        opacity=0.78,
    )
    text_layer = pdk.Layer(
        "TextLayer",
        data=regions[:12],
        get_position="[centroid_longitude, centroid_latitude]",
        get_text="display_label",
        get_size=12,
        get_color=[240, 240, 240] if color_key == "dark_color" else [30, 41, 59],
        get_alignment_baseline="'top'",
    )
    tooltip = {
        "html": (
            "<b>{tooltip_title}</b><br/>"
            "{tooltip_line_1}<br/>"
            "{tooltip_line_2}<br/>"
            "{tooltip_line_3}<br/>"
            "{tooltip_line_4}<br/>"
            "{tooltip_line_5}"
        ),
        "style": {"backgroundColor": "#0b1f33", "color": "white", "fontSize": "14px"},
    }
    return pdk.Deck(
        map_style=map_style,
        map_provider="carto",
        initial_view_state=pdk.ViewState(latitude=23.5, longitude=-102.0, zoom=4.2, pitch=0),
        layers=[region_layer, recent_layer, event_layer, text_layer],
        tooltip=tooltip,
    )

def _build_complement_event_map(payload: dict[str, object], map_style: str, zoom_enabled: bool = False) -> pdk.Deck:
    complement = _normalize_event_map_records(
        payload.get("recent_significant_events") or [],
        tr("Recorded event evidence", "Evidencia de evento registrado"),
        [80, 170, 255, 190],
    )
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=complement,
        get_position="[longitude, latitude]",
        get_fill_color="map_color",
        get_radius="safe_radius * 7500",
        radius_min_pixels=7,
        radius_max_pixels=24,
        stroked=True,
        get_line_color=[20, 20, 20, 160],
        line_width_min_pixels=1,
        pickable=True,
        opacity=0.84,
    )
    tooltip = {
        "html": "<b>{tooltip_title}</b><br/>{tooltip_line_1}<br/>{tooltip_line_2}<br/>{tooltip_line_5}",
        "style": {"backgroundColor": "#0b1f33", "color": "white", "fontSize": "14px"},
    }
    return pdk.Deck(
        map_style=map_style,
        map_provider="carto",
        initial_view_state=pdk.ViewState(latitude=23.2, longitude=-101.8, zoom=4.0, pitch=0),
        layers=[layer],
        tooltip=tooltip,
    )

def _build_plate_context_map(map_style: str, zoom_enabled: bool = False) -> pdk.Deck:
    plates = [
        {"name": "Pacific Plate", "name_es": "Placa del Pacífico", "fill": [208, 226, 255, 120], "centroid": [-117.0, 28.0], "polygon": [[-125.0, 34.0], [-119.0, 34.0], [-114.0, 29.5], [-112.0, 24.0], [-111.0, 18.0], [-118.0, 18.0], [-125.0, 24.0]], "role": "Oceanic context west of Mexico"},
        {"name": "North American Plate", "name_es": "Placa Norteamericana", "fill": [222, 244, 220, 120], "centroid": [-102.5, 25.0], "polygon": [[-118.0, 33.5], [-86.0, 33.5], [-86.0, 15.0], [-93.0, 15.0], [-96.0, 17.0], [-104.0, 18.0], [-109.0, 23.0], [-114.0, 29.0]], "role": "Continental reference context"},
        {"name": "Cocos Plate", "name_es": "Placa de Cocos", "fill": [255, 228, 210, 125], "centroid": [-100.0, 13.8], "polygon": [[-107.5, 17.0], [-94.0, 17.0], [-89.0, 11.0], [-103.0, 8.5], [-108.5, 12.5]], "role": "Pacific margin context"},
        {"name": "Rivera Plate", "name_es": "Placa de Rivera", "fill": [246, 224, 255, 125], "centroid": [-108.0, 17.8], "polygon": [[-110.5, 20.5], [-105.5, 20.3], [-103.8, 17.5], [-108.8, 16.2], [-111.0, 18.2]], "role": "Western Mexico context"},
        {"name": "Caribbean Plate", "name_es": "Placa del Caribe", "fill": [255, 242, 197, 120], "centroid": [-87.5, 18.0], "polygon": [[-92.5, 21.0], [-84.5, 21.0], [-84.0, 15.5], [-90.0, 15.5], [-92.5, 17.2]], "role": "Southeast regional context"},
    ]
    polygon_data = []
    label_data = []
    for plate in plates:
        display = plate["name_es"] if st.session_state.get("lang", "en") == "es" else plate["name"]
        polygon_data.append({
            "polygon": [[pt[0], pt[1]] for pt in plate["polygon"]],
            "fill": plate["fill"],
            "tooltip_title": display,
            "tooltip_line_1": tr("Layer: Approximate tectonic context", "Capa: Contexto tectónico aproximado"),
            "tooltip_line_2": tr("Boundary: Not authoritative geometry", "Límite: No es geometría autoritativa"),
            "tooltip_line_3": f"{tr('Role', 'Rol')}: {plate['role']}",
        })
        label_data.append({"longitude": plate["centroid"][0], "latitude": plate["centroid"][1], "display": display})
    polygon_layer = pdk.Layer(
        "PolygonLayer",
        data=polygon_data,
        get_polygon="polygon",
        get_fill_color="fill",
        get_line_color=[120, 120, 120, 180],
        line_width_min_pixels=1,
        pickable=True,
        stroked=True,
        filled=True,
    )
    label_layer = pdk.Layer(
        "TextLayer",
        data=label_data,
        get_position="[longitude, latitude]",
        get_text="display",
        get_size=15,
        get_color=[30, 30, 30],
        get_alignment_baseline="'center'",
    )
    tooltip = {
        "html": "<b>{tooltip_title}</b><br/>{tooltip_line_1}<br/>{tooltip_line_2}<br/>{tooltip_line_3}",
        "style": {"backgroundColor": "#0b1f33", "color": "white", "fontSize": "14px"},
    }
    return pdk.Deck(
        map_style=map_style,
        map_provider="carto",
        initial_view_state=pdk.ViewState(latitude=22.0, longitude=-103.0, zoom=3.8, pitch=0),
        layers=[polygon_layer, label_layer],
        tooltip=tooltip,
    )

def render_header() -> None:
    st.set_page_config(page_title=tr("Probabilistic Seismic Risk Prototype", "Prototipo Probabilístico de Riesgo Sísmico"), layout="wide")
    if "lang" not in st.session_state:
        st.session_state["lang"] = "en"
    if "section" not in st.session_state:
        st.session_state["section"] = "overview"
    inject_styles()
    st.title(tr("Probabilistic Seismic Risk Prototype", "Prototipo Probabilístico de Riesgo Sísmico"))
    st.caption(tr("Local-first prototype for bounded probabilistic seismic context analysis in Mexico.", "Prototipo local-first para análisis probabilístico acotado de contexto sísmico en México."))
    st.warning(tr("This prototype is not an official warning system and does not provide deterministic earthquake prediction.", "Este prototipo no es un sistema oficial de alerta y no proporciona predicción determinista de terremotos."))
    st.markdown(
        _badge("local-first", "blue")
        + _badge("SQLite authority", "green")
        + _badge(tr("open-source posture", "postura open-source"), "blue")
        + _badge(tr("no official warning claim", "sin afirmación de alerta oficial"), "amber"),
        unsafe_allow_html=True,
    )

def render_sidebar(bundle: dict[str, object]) -> tuple[str, str]:
    st.sidebar.title(tr("Navigation", "Navegación"))
    nav_map = {
        tr("Executive Overview", "Resumen Ejecutivo"): "overview",
        tr("Mexico Executive Map", "Mapa Ejecutivo de México"): "mexico_map",
        tr("Regional Risk View", "Vista Regional de Riesgo"): "regional",
        tr("Model Evaluation", "Evaluación del Modelo"): "evaluation",
        tr("Methodology and Traceability", "Metodología y Trazabilidad"): "methodology",
        tr("API & Integration Surface", "API y Superficie de Integración"): "api",
        tr("Future Projection", "Proyección futura"): "future",
    }
    labels = list(nav_map.keys())
    index = list(nav_map.values()).index(st.session_state["section"])
    selected = st.sidebar.radio("", labels, index=index)
    st.session_state["section"] = nav_map[selected]
    lang_choice = st.sidebar.radio(tr("Language", "Idioma"), ["English", "Español"], index=0 if st.session_state["lang"] == "en" else 1)
    st.session_state["lang"] = "en" if lang_choice == "English" else "es"
    map_theme = st.sidebar.radio(tr("Map theme", "Tema del mapa"), [tr("Light", "Claro"), tr("Dark", "Oscuro")], index=0)
    zoom_enabled = st.sidebar.toggle(tr("Enable map zoom", "Habilitar zoom en mapas"), value=False, help=tr("Keep this disabled for easier scrolling. Enable it only when you need map interaction.", "Mantén esto desactivado para un desplazamiento más cómodo. Actívalo solo cuando necesites interacción con mapas."))
    st.session_state["map_zoom_enabled"] = zoom_enabled
    authority_rel = _normalize_authority_path(bundle.get("sqlite_path", "artifacts/sqlite/seismic_prototype.db"))
    st.sidebar.markdown(f'<div class="authority-meta"><b>{tr("Maintained by", "Mantenido por")}</b>Daniel Franco</div>', unsafe_allow_html=True)
    st.sidebar.caption(tr("Authority DB", "Base de autoridad"))
    st.sidebar.markdown('<div class="path-box" title="' + authority_rel + '"><b>seismic_prototype.db</b><br><span class="subtle">SQLite structured authority</span><span class="subtle">' + _compact_authority_path(authority_rel) + '</span></div>', unsafe_allow_html=True)
    st.sidebar.markdown(f'<div class="interpretation-box"><b>{tr("Interpretation boundary", "Límite de interpretación")}</b><br><i>{tr("Public findings are descriptive and probabilistic summaries derived from the current repository dataset, its data architecture, and bounded AI/ML-oriented analytical framing.", "Los hallazgos públicos son resúmenes descriptivos y probabilísticos derivados del dataset actual del repositorio, su arquitectura de datos y un encuadre analítico acotado orientado a IA/ML.")}</i></div>', unsafe_allow_html=True)
    map_style = pdk.map_styles.CARTO_LIGHT if map_theme == tr("Light", "Claro") else pdk.map_styles.CARTO_DARK
    color_key = "light_color" if map_theme == tr("Light", "Claro") else "dark_color"
    return map_style, color_key

def render_overview() -> None:
    st.subheader(tr("Executive Overview", "Resumen Ejecutivo"))
    st.caption(tr("This section presents the solution as a publication-safe prototype: it summarizes current data coverage, bounded probabilistic findings, and the evidence artifacts that support the public surface.", "Esta sección presenta la solución como un prototipo apto para publicación: resume la cobertura actual de datos, hallazgos probabilísticos acotados y los artefactos de evidencia que respaldan la superficie pública."))
    summary = fetch_summary()
    snapshot = fetch_publication_snapshot()
    overview = snapshot.get("overview") or {}
    findings = snapshot.get("descriptive_findings") or []
    latest_feature_generation = summary.get("latest_feature_generation") or {}
    latest_model_run = summary.get("latest_model_run") or {}
    hero_plots = fetch_hero_plots()
    lookup = _plot_lookup(hero_plots)

    r1 = st.columns(4)
    with r1[0]: _present_metric("Curated Events", overview.get("total_events"))
    with r1[1]: _present_metric(tr("Coverage Years", "Años de cobertura"), overview.get("coverage_years"))
    with r1[2]: _present_metric(tr("Strongest Magnitude", "Magnitud máxima"), overview.get("strongest_magnitude"))
    with r1[3]: _present_metric(tr("Strong Events ≥ 6.0", "Eventos fuertes ≥ 6.0"), overview.get("strong_event_count"))
    r2 = st.columns(4)
    with r2[0]: _present_metric(tr("Coverage Start", "Inicio de cobertura"), _short_date(overview.get("first_event_at_utc")))
    with r2[1]: _present_metric(tr("Coverage End", "Fin de cobertura"), _short_date(overview.get("latest_event_at_utc")))
    with r2[2]: _present_metric(tr("Average Events / Year", "Promedio de eventos / año"), overview.get("avg_events_per_year"))
    with r2[3]: _present_metric(tr("Feature Window", "Ventana de features"), latest_feature_generation.get("window_spec"))
    r3 = st.columns(3)
    with r3[0]: _present_metric(tr("Feature Generation Status", "Estado de generación de features"), latest_feature_generation.get("status"))
    with r3[1]: _present_metric(tr("Model Run Status", "Estado de ejecución del modelo"), _display_state(latest_model_run.get("status"), tr("Publication-limited baseline", "Baseline limitado para publicación")))
    with r3[2]: _present_metric(tr("Model Family", "Familia de modelo"), _display_state(latest_model_run.get("model_family"), "baseline_random_forest"))

    hero = st.columns(2)
    with hero[0]:
        st.markdown(f'<div class="demonstrates-box"><b>{tr("What this prototype demonstrates", "Qué demuestra este prototipo")}</b><br><br>{tr("A governed, local-first, publication-safe architecture that organizes seismic context through reproducible artifacts, structured authority, bounded analytics, and interpretable delivery.", "Una arquitectura gobernada, local-first y segura para publicación que organiza contexto sísmico mediante artefactos reproducibles, autoridad estructurada, analítica acotada y entrega interpretable.")}</div>', unsafe_allow_html=True)
    with hero[1]:
        st.markdown(f'<div class="warning-box"><b>{tr("What this prototype does not claim", "Qué no afirma este prototipo")}</b><br><br>{tr("It does not claim official warning capability, deterministic earthquake prediction, or authoritative geophysical mapping. Its public value is disciplined engineering communication.", "No afirma capacidad oficial de alerta, predicción determinista de terremotos ni cartografía geofísica autoritativa. Su valor público es la comunicación disciplinada de ingeniería.")}</div>', unsafe_allow_html=True)

    _section_intro("Descriptive Findings From the Current Dataset", "Hallazgos descriptivos del dataset actual", "These findings are intentionally emphasized because they are the highest-value takeaways for a reader who needs fast orientation without overinterpreting the prototype.", "Estos hallazgos se enfatizan intencionalmente porque son las conclusiones de mayor valor para un lector que necesita orientación rápida sin sobreinterpretar el prototipo.")
    for item in findings[:4]:
        st.markdown(f'<div class="findings-box">{_esc(item)}</div>', unsafe_allow_html=True)

    _section_intro("Visual Evidence Highlights", "Visuales de evidencia prioritarios", "The overview only surfaces the three visuals that best orient a first-time reviewer. Additional technical visuals appear in later sections where they are easier to interpret.", "El resumen solo muestra los tres visuales que mejor orientan a un revisor por primera vez. Los visuales técnicos adicionales aparecen después, donde son más fáciles de interpretar.")
    priority_specs = [
        ("pipeline_trace.png", tr("Pipeline Trace", "Trazabilidad del pipeline"), tr("Explains how curated evidence becomes structured authority, features, and publication artifacts.", "Explica cómo la evidencia curada se convierte en autoridad estructurada, features y artefactos de publicación.")),
        ("metrics_panel.png", tr("Metrics Panel", "Panel de métricas"), tr("Compact executive summary of persisted indicators used across the public surface.", "Resumen ejecutivo compacto de indicadores persistidos usados en toda la superficie pública.")),
        ("probabilistic_risk_map.png", tr("Probabilistic Risk Map", "Mapa probabilístico de riesgo"), tr("Prototype ranking of regional concentration intended for interpretive reading rather than official hazard classification.", "Ranking del prototipo sobre concentración regional pensado para lectura interpretativa y no como clasificación oficial de riesgo.")),
    ]
    for filename, title, description in priority_specs:
        img = lookup.get(filename)
        if img:
            cols = st.columns([1.05, 1.45])
            with cols[0]:
                st.markdown(f'<div class="narrative-box"><b>{title}</b><br><br>{description}</div>', unsafe_allow_html=True)
            with cols[1]:
                st.image(img, width="stretch")
    st.markdown(f'<div class="section-jump">{tr("Continue to Mexico Executive Map for geographic reading, Model Evaluation for bounded metrics, and Methodology and Traceability for the canonical publication inventory.", "Continúa hacia Mapa Ejecutivo de México para la lectura geográfica, Evaluación del Modelo para métricas acotadas, y Metodología y Trazabilidad para el inventario canónico de publicación.")}</div>', unsafe_allow_html=True)

def render_mexico_map(map_style: str, color_key: str) -> None:
    st.subheader(tr("Mexico Executive Map", "Mapa Ejecutivo de México"))
    payload = fetch_executive_mexico_map_payload()
    snapshot = fetch_publication_snapshot()
    overview = payload.get("overview") or {}
    strongest_event = payload.get("strongest_event") or {}
    top_zones = payload.get("top_affected_zones") or []
    tectonic_context = payload.get("tectonic_context") or []
    monthly_activity = snapshot.get("monthly_activity") or {}
    yearly_strong = snapshot.get("yearly_strong_activity") or {}
    regional_concentration = snapshot.get("regional_concentration") or []
    all_months = monthly_activity.get("all_events") or []
    strong_months = monthly_activity.get("strong_events") or []
    strong_years = yearly_strong.get("strong_counts_by_year") or []

    row = st.columns(4)
    with row[0]: _present_metric("Total Curated Events", overview.get("total_events"))
    with row[1]: _present_metric(tr("Coverage Start", "Inicio de cobertura"), _short_date(overview.get("first_event_at_utc")))
    with row[2]: _present_metric(tr("Coverage End", "Fin de cobertura"), _short_date(overview.get("latest_event_at_utc")))
    with row[3]: _present_metric(tr("Strongest Magnitude", "Magnitud máxima"), overview.get("strongest_magnitude"))

    st.markdown(tr(
        "This map presents a **probabilistic-descriptive national view** of the current repository dataset. It helps the reader interpret concentration, stronger events, prototype-region prominence, and bounded AI/ML-oriented analytical reading without implying official hazard or warning claims.",
        "Este mapa presenta una **vista nacional probabilístico-descriptiva** del dataset actual del repositorio. Ayuda a interpretar concentración, eventos fuertes, prominencia regional del prototipo y lectura analítica acotada orientada a IA/ML sin implicar afirmaciones oficiales de peligro o alerta.",
    ))
    st.pydeck_chart(_build_mexico_map(payload, map_style, color_key, st.session_state.get("map_zoom_enabled", False)), width="stretch")
    top_zone = top_zones[0] if top_zones else {}
    st.markdown(
        _map_detail_panel(
            tr("Executive map detail panel", "Panel ejecutivo de detalle del mapa"),
            [
                (tr("Highest concentration", "Mayor concentración"), top_zone.get("label") or top_zone.get("reference_geography") or tr("Not published", "No publicado")),
                (tr("Total events", "Eventos totales"), top_zone.get("event_count_total") or overview.get("total_events")),
                (tr("Strongest event", "Evento más fuerte"), strongest_event.get("magnitude_value") or overview.get("strongest_magnitude")),
                (tr("Interpretation", "Interpretación"), tr("Descriptive prototype view", "Vista descriptiva del prototipo")),
            ],
            "blue",
        ),
        unsafe_allow_html=True,
    )
    st.info(payload.get("map_note", tr("Prototype map note unavailable.", "Nota del mapa no disponible.")))

    _section_intro(
        "Complementary Context Maps",
        "Mapas contextuales complementarios",
        "These supporting maps are intentionally separated to avoid visual crowding and to distinguish event-level evidence from tectonic context.",
        "Estos mapas de apoyo se separan intencionalmente para evitar saturación visual y distinguir evidencia a nivel evento del contexto tectónico.",
    )
    st.markdown(f"**{tr('Complementary Recorded Events Map', 'Mapa complementario de eventos registrados')}**")
    st.caption(tr(
        "This map complements the executive circles by showing recorded event-level distribution and magnitude in a cleaner standalone view.",
        "Este mapa complementa los círculos ejecutivos al mostrar distribución y magnitud a nivel evento en una vista independiente más limpia.",
    ))
    st.pydeck_chart(_build_complement_event_map(payload, map_style, st.session_state.get("map_zoom_enabled", False)), width="stretch")

    st.markdown(f"**{tr('Tectonic Plate Context Schematic', 'Esquema de contexto de placas tectónicas')}**")
    st.caption(tr(
        "This schematic shows approximate relationship, position, and coexistence of the main tectonic plates relevant to Mexico. It is a contextual engineering aid, not an authoritative geophysical boundary product.",
        "Este esquema muestra la relación aproximada, posición y coexistencia de las principales placas tectónicas relevantes para México. Es una ayuda contextual de ingeniería, no un producto geofísico autoritativo de límites.",
    ))
    st.pydeck_chart(_build_plate_context_map(map_style, st.session_state.get("map_zoom_enabled", False)), width="stretch")

    _section_intro(
        "Descriptive Probabilistic Reading",
        "Lectura probabilística descriptiva",
        "These deductions are bounded by the current persisted dataset and should be read as interpretive support rather than deterministic conclusions.",
        "Estas deducciones están acotadas por el dataset persistido actual y deben leerse como soporte interpretativo, no como conclusiones deterministas.",
    )
    bullets = []
    peak_month = _top_item(all_months, "event_count")
    peak_strong_month = _top_item(strong_months, "strong_event_count")
    peak_strong_year = _top_item(strong_years, "strong_event_count")
    if top_zones:
        bullets.append(f"{tr('The current dataset shows the strongest historical concentration in', 'El dataset actual muestra la concentración histórica más fuerte en')} {top_zones[0].get('reference_geography')}.")
    if peak_month:
        bullets.append(f"{tr('Month', 'El mes')} {peak_month.get('month')} {tr('has the highest total recorded activity concentration in the current dataset.', 'presenta la mayor concentración total de actividad registrada en el dataset actual.')}")
    if peak_strong_month:
        bullets.append(f"{tr('Month', 'El mes')} {peak_strong_month.get('month')} {tr('has the highest concentration of strong events in the current dataset.', 'presenta la mayor concentración de eventos fuertes en el dataset actual.')}")
    if peak_strong_year:
        bullets.append(f"{tr('Year', 'El año')} {peak_strong_year.get('year')} {tr('has the highest count of strong recorded events under the current descriptive threshold.', 'tiene el mayor conteo de eventos fuertes registrados bajo el umbral descriptivo actual.')}")
    for item in bullets:
        st.markdown(f"- {item}")

    _section_intro(
        "Temporal and Regional Views",
        "Vistas temporales y regionales",
        "The charts below are vertically separated for readability in export and present monthly, yearly, and regional concentration summaries from the current dataset.",
        "Las gráficas siguientes se separan verticalmente para mejorar legibilidad en exportación y presentan resúmenes mensuales, anuales y regionales del dataset actual.",
    )
    st.markdown(f"**{tr('Monthly Recorded Activity', 'Actividad mensual registrada')}**")
    st.caption(tr("Recorded monthly concentration in the current dataset.", "Concentración mensual registrada en el dataset actual."))
    st.bar_chart(_monthly_df(all_months, "event_count", tr("Recorded events", "Eventos registrados")), height=260)
    st.caption(tr("Interpretation: this chart highlights the strongest month-level concentration in the persisted historical record and should be read as descriptive context only.", "Interpretación: esta gráfica resalta la concentración mensual más fuerte del registro histórico persistido y debe leerse solo como contexto descriptivo."))
    st.markdown(f"**{tr('Strong Events by Month', 'Eventos fuertes por mes')}**")
    st.caption(tr("Strong-event concentration using the current descriptive threshold.", "Concentración de eventos fuertes usando el umbral descriptivo actual."))
    st.bar_chart(_monthly_df(strong_months, "strong_event_count", tr("Strong events", "Eventos fuertes")), height=260)
    st.caption(tr("Interpretation: this view shows when stronger recorded events cluster under the current descriptive threshold, without implying seasonality or forecasting.", "Interpretación: esta vista muestra cuándo se agrupan eventos fuertes registrados bajo el umbral descriptivo actual, sin implicar estacionalidad ni pronóstico."))
    st.markdown(f"**{tr('Strong Events by Year', 'Eventos fuertes por año')}**")
    st.caption(tr("Yearly distribution of strong recorded events in the current dataset.", "Distribución anual de eventos fuertes registrados en el dataset actual."))
    st.line_chart(_yearly_df(strong_years, "strong_event_count", tr("Strong events", "Eventos fuertes")), height=280)
    st.caption(tr("Interpretation: this yearly line emphasizes historically stronger years in the bounded dataset and should be used for temporal context, not predictive inference.", "Interpretación: esta línea anual enfatiza los años históricamente más fuertes del dataset acotado y debe usarse para contexto temporal, no para inferencia predictiva."))
    st.markdown(f"**{tr('Top Regional Concentration', 'Mayor concentración regional')}**")
    st.caption(tr("Most prominent prototype regions by total recorded events.", "Regiones del prototipo más prominentes por total de eventos registrados."))
    st.bar_chart(_regional_chart_df(regional_concentration, "event_count_total", tr("Recorded events", "Eventos registrados")), height=280)
    st.caption(tr("Interpretation: this comparison ranks the most prominent prototype regions by total recorded events in the current publication state.", "Interpretación: esta comparación ordena las regiones del prototipo más prominentes por total de eventos registrados en el estado actual de publicación."))

    if strongest_event:
        _section_intro(
            "Most Notable Historical Event",
            "Evento histórico más notable",
            "This is the strongest event currently represented in the persisted dataset and is shown as historical reference only.",
            "Este es el evento más fuerte actualmente representado en el dataset persistido y se muestra solo como referencia histórica.",
        )
        er = st.columns(5)
        with er[0]: _present_metric(tr("Occurred At", "Fecha"), _short_date(strongest_event.get("occurred_at_utc")))
        with er[1]: _present_metric(tr("Magnitude", "Magnitud"), strongest_event.get("magnitude_value"))
        with er[2]: _present_metric(tr("Depth (km)", "Profundidad (km)"), strongest_event.get("depth_km"))
        with er[3]: _present_metric(tr("Reference Geography", "Geografía de referencia"), strongest_event.get("reference_geography"))
        with er[4]: _present_metric(tr("Political Division", "División política"), strongest_event.get("political_division"))

    _section_intro(
        "Political and Prototype Context",
        "Contexto político y del prototipo",
        "Political-division names shown here are approximate contextual references derived from current prototype aggregation logic. They are not official boundary geometries.",
        "Los nombres de división política mostrados aquí son referencias contextuales aproximadas derivadas de la lógica actual de agregación del prototipo. No son geometrías oficiales de límites.",
    )
    if top_zones:
        rows = [{
            tr("Reference Geography", "Geografía de referencia"): z.get("reference_geography"),
            tr("Political Division", "División política"): z.get("political_division"),
            tr("Region Code", "Código regional"): z.get("region_code"),
            tr("Total Events", "Eventos totales"): z.get("event_count_total"),
            tr("Max Magnitude", "Magnitud máxima"): z.get("max_magnitude"),
        } for z in top_zones]
        st.markdown(_html_table(_clean_rows(rows), headers=list(rows[0].keys())), unsafe_allow_html=True)

    _section_intro(
        "Prototype Tectonic Context",
        "Contexto tectónico del prototipo",
        "These labels summarize how the prototype interprets tectonic context using current persisted bands. They are contextual descriptors, not authoritative plate-boundary geometries.",
        "Estas etiquetas resumen cómo el prototipo interpreta el contexto tectónico usando las bandas persistidas actuales. Son descriptores contextuales, no geometrías autoritativas de límites de placas.",
    )
    if tectonic_context:
        rows = [{
            tr("Reference Geography", "Geografía de referencia"): item.get("label"),
            tr("Political Division", "División política"): item.get("political_division"),
            tr("Tectonic Layer", "Capa tectónica"): item.get("tectonic_layer"),
            tr("Risk Band", "Banda de riesgo"): item.get("risk_band"),
            tr("Executive Risk Index", "Índice ejecutivo de riesgo"): item.get("executive_risk_index"),
        } for item in tectonic_context[:8]]
        st.markdown(_html_table(_clean_rows(rows), headers=list(rows[0].keys())), unsafe_allow_html=True)



def render_regional() -> None:
    st.subheader(tr("Regional Risk View", "Vista Regional de Riesgo"))
    st.caption(tr("Codes beginning with MX_ indicate named prototype bands. Codes beginning with bin_ indicate grid-based spatial cells used for bounded aggregation. Both are prototype semantics and not official territorial categories.", "Los códigos que comienzan con MX_ indican bandas nombradas del prototipo. Los códigos que comienzan con bin_ indican celdas espaciales basadas en cuadrícula usadas para agregación acotada. Ambos son semánticas del prototipo y no categorías territoriales oficiales."))
    st.markdown(f'<div class="narrative-box"><b>{tr("How to read this section", "Cómo leer esta sección")}</b><br><br>{tr("Use this section to inspect one prototype region at a time. The goal is not to imply official administrative zoning, but to explain how the prototype groups space for bounded regional interpretation.", "Usa esta sección para inspeccionar una región del prototipo a la vez. El objetivo no es implicar zonificación administrativa oficial, sino explicar cómo el prototipo agrupa el espacio para interpretación regional acotada.")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="narrative-box"><b>{tr("Experimental scope", "Alcance experimental")}</b><br><br>{tr("The intent of this section is not to create a tectonic study. It presents the results of a reproducible, professional, and idempotent process that can later expand with additional ML and AI stages.", "La intención de esta sección no es crear un estudio tectónico. Presenta los resultados de un proceso reproducible, profesional e idempotente que después puede expandirse con etapas adicionales de ML e IA.")}<br><br>{tr("In engineering terms, this regional view is a governed prototype surface that may grow horizontally and vertically through on-premise or cloud integrations once those stages are formally implemented.", "En términos de ingeniería, esta vista regional es una superficie de prototipo gobernada que puede crecer horizontal y verticalmente mediante integraciones on-premise o cloud una vez que esas etapas se implementen formalmente.")}</div>', unsafe_allow_html=True)

    snapshot = fetch_publication_snapshot()
    meta = _region_meta(snapshot)
    region_codes = fetch_region_codes()
    if not region_codes:
        st.info(tr("No persisted region features are available yet.", "Aún no hay features regionales persistidas."))
        return

    filter_scope = st.radio(
        tr("Region scope", "Alcance regional"),
        [tr("All regions", "Todas las regiones"), tr("Named prototype bands", "Bandas nombradas del prototipo"), tr("Grid bins", "Bins de cuadrícula")],
        horizontal=True,
    )
    if filter_scope == tr("Named prototype bands", "Bandas nombradas del prototipo"):
        filtered = [c for c in region_codes if c.startswith("MX_")]
    elif filter_scope == tr("Grid bins", "Bins de cuadrícula"):
        filtered = [c for c in region_codes if c.startswith("bin_")]
    else:
        filtered = region_codes

    selected = st.selectbox(
        tr("Select region or prototype band", "Selecciona región o banda del prototipo"),
        filtered,
        format_func=lambda c: _friendly_region_label(c, meta),
        help=tr("Named entries such as MX_CENTRAL describe prototype bands. Entries beginning with bin_ describe bounded grid cells used for spatial aggregation and not official administrative areas.", "Las entradas tipo MX_CENTRAL describen bandas del prototipo. Las entradas que comienzan con bin_ describen celdas de cuadrícula usadas para agregación espacial acotada y no áreas administrativas oficiales."),
    )

    regional_concentration = snapshot.get("regional_concentration") or []
    region_payload = fetch_region_latest(selected)
    if region_payload is None:
        st.warning(f"No latest feature row found for {selected}.")
        return
    matching = next((item for item in regional_concentration if item.get("region_code") == selected), None)

    reference_geography = (matching or {}).get("reference_geography") or region_payload.get("reference_geography") or meta.get(selected, {}).get("reference_geography")
    political_division = (matching or {}).get("political_division") or region_payload.get("political_division") or meta.get(selected, {}).get("political_division")
    tectonic_layer = (matching or {}).get("tectonic_layer") or region_payload.get("tectonic_layer") or meta.get(selected, {}).get("tectonic_layer")
    event_count_display = (matching or {}).get("event_count_total") or region_payload.get("event_count")
    strong_event_display = (matching or {}).get("strong_event_count")
    max_mag_display = (matching or {}).get("max_magnitude") or region_payload.get("max_magnitude")
    risk_index_display = (matching or {}).get("executive_risk_index") or region_payload.get("target_risk_score") or tr("Publication-limited", "Limitado para publicación")

    r1 = st.columns(2)
    with r1[0]: _present_metric(tr("Reference Geography", "Geografía de referencia"), reference_geography)
    with r1[1]: _present_metric(tr("Political Division", "División política"), political_division)

    r2 = st.columns(4)
    with r2[0]: _present_metric(tr("Event Count", "Conteo de eventos"), event_count_display)
    with r2[1]: _present_metric(tr("Strong Events", "Eventos fuertes"), strong_event_display)
    with r2[2]: _present_metric(tr("Mean Magnitude", "Magnitud media"), region_payload.get("mean_magnitude"))
    with r2[3]: _present_metric(tr("Max Magnitude", "Magnitud máxima"), max_mag_display)

    r3 = st.columns(3)
    with r3[0]: _present_metric(tr("Tectonic Layer", "Capa tectónica"), tectonic_layer)
    with r3[1]: _present_metric(tr("Days Since Last Event", "Días desde el último evento"), region_payload.get("days_since_last_event"))
    with r3[2]: _present_metric(tr("Executive Risk Index", "Índice ejecutivo de riesgo"), risk_index_display)

    if matching:
        _section_intro(
            "Regional Interpretation Note",
            "Nota de interpretación regional",
            "This reading provides a specific narrative for the selected region instead of repeating the same generic visuals without context.",
            "Esta lectura proporciona una narrativa específica para la región seleccionada en lugar de repetir los mismos visuales genéricos sin contexto.",
        )
        bullets = [
            f"{tr('This prototype region is historically associated with', 'Esta región del prototipo está históricamente asociada con')} {matching.get('reference_geography')}.",
            f"{tr('It aggregates', 'Agrega')} {_safe_metric_value(matching.get('event_count_total'))} {tr('recorded events in the current dataset.', 'eventos registrados en el dataset actual.')}",
            f"{tr('It contains', 'Contiene')} {_safe_metric_value(matching.get('strong_event_count'))} {tr('events at or above the current strong-event threshold.', 'eventos en o por encima del umbral actual de eventos fuertes.')}",
            f"{tr('Its historical maximum recorded magnitude in the current dataset is', 'Su magnitud máxima histórica registrada en el dataset actual es')} {_safe_metric_value(matching.get('max_magnitude'))}.",
        ]
        for item in bullets:
            st.markdown(f"- {item}")

    _section_intro(
        "Regional Concentration Comparison",
        "Comparación de concentración regional",
        "This chart situates the selected region within the most prominent prototype regions in the current dataset using shorter labels for export clarity.",
        "Esta gráfica sitúa la región seleccionada dentro de las regiones más prominentes del prototipo en el dataset actual usando etiquetas cortas para mayor claridad en exportación.",
    )
    st.bar_chart(_regional_chart_df(regional_concentration, "event_count_total", tr("Recorded events", "Eventos registrados")), height=300)
    st.caption(tr("Interpretation: this bar chart positions the selected region against the most concentrated prototype regions in the persisted dataset.", "Interpretación: esta gráfica posiciona la región seleccionada frente a las regiones del prototipo con mayor concentración en el dataset persistido."))

    _section_intro(
        "Selected Region Summary",
        "Resumen de la región seleccionada",
        "This compact key-value view preserves clarity in PDF export and keeps the meaning of the selected region explicit.",
        "Esta vista compacta tipo clave-valor preserva claridad en exportación PDF y mantiene explícito el significado de la región seleccionada.",
    )
    summary_rows = _kv_rows([
        (tr("Region code", "Código regional"), selected),
        (tr("Display label", "Etiqueta visible"), _friendly_region_label(selected, meta)),
        (tr("Reference geography", "Geografía de referencia"), reference_geography),
        (tr("Political division", "División política"), political_division),
        (tr("Tectonic layer", "Capa tectónica"), tectonic_layer),
        (tr("Mean magnitude", "Magnitud media"), region_payload.get("mean_magnitude")),
        (tr("Event count", "Conteo de eventos"), event_count_display),
        (tr("Executive risk index", "Índice ejecutivo de riesgo"), risk_index_display),
    ])
    st.markdown(_html_table(summary_rows, headers=["Field", "Value"]), unsafe_allow_html=True)


def render_evaluation() -> None:
    st.subheader(tr("Model Evaluation", "Evaluación del Modelo"))
    evaluation = fetch_evaluation()
    metrics = evaluation.get("metrics") or {}
    has_eval = evaluation.get("evaluation_report_id") is not None and bool(metrics)
    _section_intro("Prototype Objective and Evaluation Scope", "Objetivo del prototipo y alcance de la evaluación", "The objective here is not to publish a scientific earthquake study. The prototype demonstrates a local-first data architecture, bounded probabilistic aggregation, and a governed publication surface for communicating regional seismic context.", "El objetivo aquí no es publicar un estudio científico de terremotos. El prototipo demuestra una arquitectura de datos local-first, agregación probabilística acotada y una superficie de publicación gobernada para comunicar contexto sísmico regional.")
    for item in [tr("It is a prototype for probabilistic regional risk communication, not an operational warning system.", "Es un prototipo para comunicación probabilística de riesgo regional, no un sistema operativo de alerta."), tr("It is not a deterministic earthquake prediction engine.", "No es un motor de predicción determinista de terremotos."), tr("It is not a formal geophysical study intended to replace hazard maps, official seismological analysis, or civil-protection procedures.", "No es un estudio geofísico formal destinado a sustituir mapas de riesgo, análisis sismológicos oficiales o procedimientos de protección civil."), tr("Its value lies in architecture, data traceability, bounded analytics, and interpretable publication output.", "Su valor está en la arquitectura, la trazabilidad de datos, la analítica acotada y la salida de publicación interpretable.")]:
        st.markdown(f"- {item}")
    st.markdown(f'<div class="narrative-box"><b>{tr("Engineering interpretation", "Interpretación de ingeniería")}</b><br><br>{tr("From an engineering perspective, this section demonstrates governance discipline: the system only elevates what is persisted, traceable, and presentation-safe. Missing evidence is treated as a managed limitation instead of being hidden or replaced by speculation.", "Desde una perspectiva de ingeniería, esta sección demuestra disciplina de gobernanza: el sistema solo eleva lo que está persistido, trazable y es seguro para presentación. La evidencia faltante se trata como una limitación gestionada en lugar de ocultarse o sustituirse por especulación.")}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="hero-box"><b>{tr("Publication badges", "Badges de publicación")}</b><br><br>'
        + _status_badge(evaluation.get("model_run_id"), tr("publication-limited", "publication-limited"))
        + _status_badge(metrics.get("roc_auc"), tr("not published in current release", "not published in current release"))
        + _badge(tr("local-first authority", "autoridad local-first"), "blue")
        + _badge(tr("bounded interpretation", "interpretación acotada"), "green")
        + '</div>',
        unsafe_allow_html=True,
    )
    _section_intro("Current Methodological Elements", "Elementos metodológicos actuales", "The current publication surface is supported by engineering and analytical choices that remain bounded and auditable.", "La superficie de publicación actual está respaldada por decisiones de ingeniería y analítica que permanecen acotadas y auditables.")
    for item in [tr("SQLite as local structured authority for prototype publication artifacts.", "SQLite como autoridad estructurada local para artefactos de publicación del prototipo."), tr("Regional aggregation and grid/bin abstractions to support local-first spatial summarization.", "Agregación regional y abstracciones por cuadrícula/bin para resumir espacialmente de forma local-first."), tr("Temporal windows and derived features compatible with AI/ML-oriented workflows.", "Ventanas temporales y variables derivadas compatibles con flujos orientados a IA/ML."), tr("Persisted reports and plots used as public evidence rather than ad hoc narrative claims.", "Reportes y plots persistidos usados como evidencia pública en lugar de afirmaciones narrativas ad hoc.")]:
        st.markdown(f"- {item}")
    if not has_eval:
        st.info(tr("Persisted evaluation artifacts are not currently available for publication. This section remains bounded by the current repository state and intentionally avoids fabricated metrics.", "Los artefactos persistidos de evaluación no están actualmente disponibles para publicación. Esta sección permanece acotada por el estado actual del repositorio y evita intencionalmente métricas fabricadas."))
        row = st.columns(3)
        with row[0]: _present_metric(tr("Evaluation State", "Estado de evaluación"), tr("Publication-limited baseline", "Baseline limitado para publicación"))
        with row[1]: _present_metric(tr("Model Run Reference", "Referencia de ejecución"), _display_state(evaluation.get("model_run_id"), "baseline_publication_limited"))
        with row[2]: _present_metric(tr("Publication Policy", "Política de publicación"), tr("Bounded publication enforced", "Publicación acotada activa"))
        _section_intro("Current Publication Posture", "Postura actual de publicación", "Evaluation is intentionally shown as governed and bounded. Missing artifacts are treated as explicit limitations rather than hidden or fabricated.", "La evaluación se muestra intencionalmente como gobernada y acotada. Los artefactos faltantes se tratan como limitaciones explícitas y no se ocultan ni se fabrican.")
        rows = [
            {tr("Component", "Componente"): tr("Persisted evaluation metrics", "Métricas persistidas de evaluación"), tr("Status", "Estado"): tr("Baseline metrics published", "Métricas baseline publicadas"), tr("Interpretation", "Interpretación"): tr("Bounded baseline metrics are shown without fabricating unavailable evidence.", "Se muestran métricas baseline acotadas sin fabricar evidencia no disponible.")},
            {tr("Component", "Componente"): tr("Evaluation plots", "Plots de evaluación"), tr("Status", "Estado"): tr("Publication-limited but available", "Disponibles con límite de publicación"), tr("Interpretation", "Interpretación"): tr("Plots are derived from persisted artifacts and remain bounded.", "Los plots se derivan de artefactos persistidos y permanecen acotados.")},
            {tr("Component", "Componente"): tr("Public communication policy", "Política de comunicación pública"), tr("Status", "Estado"): tr("Active", "Activa"), tr("Interpretation", "Interpretación"): tr("Fallback remains explicit and sober.", "El fallback permanece explícito y sobrio.")},
        ]
        st.markdown(_html_table(rows, headers=list(rows[0].keys())), unsafe_allow_html=True)
    else:
        row1 = st.columns(4)
        with row1[0]: _present_metric(tr("Eval ID", "ID eval."), _display_state(evaluation.get("evaluation_report_id"), "publication_limited_baseline"))
        with row1[1]: _present_metric(tr("Model Run", "Ejecución"), _display_state(evaluation.get("model_run_id"), "baseline_random_forest"))
        with row1[2]: _present_metric("ROC AUC", _publication_state(metrics.get("roc_auc"), tr("Not in release", "Fuera de la versión")))
        with row1[3]: _present_metric("PR AUC", _publication_state(metrics.get("pr_auc"), tr("Not in release", "Fuera de la versión")))
        row2 = st.columns(3)
        with row2[0]: _present_metric("F1", _publication_state(metrics.get("f1_score"), tr("Not in release", "Fuera de la versión")))
        with row2[1]: _present_metric("Brier", _publication_state(metrics.get("brier_score"), tr("Not in release", "Fuera de la versión")))
        with row2[2]: _present_metric(tr("Bal. Accuracy", "Exactitud balanceada"), _publication_state(metrics.get("balanced_accuracy"), tr("Not in release", "Fuera de la versión")))
        captions = {
            "ROC Curve": tr("Receiver operating characteristic published from the current bounded baseline.", "Curva ROC publicada desde la baseline acotada actual."),
            "Precision-Recall Curve": tr("Precision-recall view for the current publication-limited baseline.", "Vista precision-recall para la baseline actual limitada para publicación."),
            "Probability Histogram": tr("Predicted probability histogram used as bounded diagnostic support.", "Histograma de probabilidad predicha usado como soporte diagnóstico acotado."),
        }
        for plot in fetch_evaluation_plots():
            st.markdown(f"**{plot['title']}**")
            st.caption(captions.get(plot["title"], tr("Persisted evaluation visual.", "Visual persistido de evaluación.")))
            st.image(plot["path"], width="stretch")


def render_methodology() -> None:
    st.subheader(tr("Methodology and Traceability", "Metodología y Trazabilidad"))
    st.caption(tr("This section explains why the publication surface exists, how its claims should be interpreted, and which canonical components support the prototype.", "Esta sección explica por qué existe la superficie de publicación, cómo deben interpretarse sus afirmaciones y qué componentes canónicos sostienen el prototipo."))

    bundle = fetch_publication_bundle()
    snapshot = bundle.get("publication_snapshot") or {}
    summary = bundle.get("summary") or {}
    hero_plots = bundle.get("hero_plots") or []
    hero_reports = bundle.get("hero_reports") or []
    region_codes = bundle.get("region_codes") or []
    plot_rows, report_rows = _artifact_rows(hero_plots, hero_reports)

    _section_intro(
        "Canonical Solution Description",
        "Descripción canónica de la solución",
        "This public surface represents a bounded, local-first solution for organizing, aggregating, and presenting probabilistic seismic context in Mexico.",
        "Esta superficie pública representa una solución local-first y acotada para organizar, agregar y presentar contexto sísmico probabilístico en México.",
    )
    for item in [
        tr("Raw event data is preserved as immutable evidence.", "Los datos crudos de eventos se preservan como evidencia inmutable."),
        tr("SQLite acts as structured prototype authority for publication and retrieval.", "SQLite actúa como autoridad estructurada del prototipo para publicación y consulta."),
        tr("The web surface exists to communicate bounded findings with low cognitive friction.", "La superficie web existe para comunicar hallazgos acotados con baja fricción cognitiva."),
        tr("Cloud and production-scale warning semantics remain explicitly out of scope.", "La nube y las semánticas de alerta de producción permanecen explícitamente fuera de alcance."),
    ]:
        st.markdown(f"- {item}")

    st.markdown(f'<div class="narrative-box"><b>{tr("Engineering council reading", "Lectura de consejo de ingeniería")}</b><br><br>{tr("From a governance and architecture perspective, the publication layer should privilege coherence, bounded claims, and traceable evidence over decorative complexity. This is why the surface explicitly separates descriptive findings, contextual maps, regional abstractions, and evaluation posture.", "Desde una perspectiva de gobernanza y arquitectura, la capa de publicación debe privilegiar la coherencia, las afirmaciones acotadas y la evidencia trazable por encima de la complejidad decorativa. Por eso la superficie separa explícitamente hallazgos descriptivos, mapas contextuales, abstracciones regionales y postura de evaluación.")}</div>', unsafe_allow_html=True)

    row = st.columns(4)
    with row[0]: _present_metric(tr("Authority DB", "Base de autoridad"), "seismic_prototype.db")
    with row[1]: _present_metric(tr("Hero Plots", "Plots principales"), len(hero_plots))
    with row[2]: _present_metric(tr("Hero Reports", "Reportes principales"), len(hero_reports))
    with row[3]: _present_metric(tr("Indexed Regions", "Regiones indexadas"), len(region_codes))

    _section_intro(
        "Ingestion and Treatment Cycle",
        "Ciclo de ingesta y tratamiento",
        "The diagram and table below make the prototype lineage explicit: every public surface should be read as the result of bounded ingestion, validation, structured authority, feature generation, regional aggregation, and publication controls.",
        "El diagrama y la tabla siguientes explicitan el linaje del prototipo: toda superficie pública debe leerse como resultado de ingesta acotada, validación, autoridad estructurada, generación de features, agregación regional y controles de publicación.",
    )
    methodology_lookup = _plot_lookup(hero_plots)
    methodology_plot = methodology_lookup.get("methodology_traceability_cycle.png") or methodology_lookup.get("methodology_traceability_cycle.svg")
    if methodology_plot:
        st.image(methodology_plot, width="stretch")
    cycle_rows = [
        {tr("Stage", "Etapa"): tr("Raw evidence", "Evidencia cruda"), tr("Engineering contribution", "Aportación de ingeniería"): tr("Preserves original dataset lineage and separates source material from derived artifacts.", "Preserva el linaje del dataset original y separa el material fuente de los artefactos derivados."), tr("Evidence boundary", "Límite de evidencia"): tr("Not modified by presentation logic.", "No se modifica por lógica de presentación.")},
        {tr("Stage", "Etapa"): tr("Validation and normalization", "Validación y normalización"), tr("Engineering contribution", "Aportación de ingeniería"): tr("Reduces malformed records and prepares consistent fields for analysis.", "Reduce registros malformados y prepara campos consistentes para análisis."), tr("Evidence boundary", "Límite de evidencia"): tr("Does not invent missing truth.", "No inventa verdad faltante.")},
        {tr("Stage", "Etapa"): tr("SQLite structured authority", "Autoridad estructurada SQLite"), tr("Engineering contribution", "Aportación de ingeniería"): tr("Provides local-first retrieval, traceability, and reproducible publication payloads.", "Proporciona consulta local-first, trazabilidad y payloads de publicación reproducibles."), tr("Evidence boundary", "Límite de evidencia"): tr("Prototype authority, not institutional authority.", "Autoridad del prototipo, no autoridad institucional.")},
        {tr("Stage", "Etapa"): tr("Feature generation", "Generación de features"), tr("Engineering contribution", "Aportación de ingeniería"): tr("Transforms curated events into analytical variables suitable for bounded modeling.", "Transforma eventos curados en variables analíticas aptas para modelado acotado."), tr("Evidence boundary", "Límite de evidencia"): tr("Prototype-grade analytical features.", "Features analíticas de grado prototipo.")},
        {tr("Stage", "Etapa"): tr("Regional aggregation", "Agregación regional"), tr("Engineering contribution", "Aportación de ingeniería"): tr("Creates interpretable regional summaries and concentration views.", "Crea resúmenes regionales interpretables y vistas de concentración."), tr("Evidence boundary", "Límite de evidencia"): tr("Not official zoning or hazard mapping.", "No es zonificación oficial ni mapeo de peligro.")},
        {tr("Stage", "Etapa"): tr("Evaluation and publication surface", "Evaluación y superficie de publicación"), tr("Engineering contribution", "Aportación de ingeniería"): tr("Communicates bounded model posture, findings, API surfaces, and review artifacts.", "Comunica postura acotada del modelo, hallazgos, superficies API y artefactos de revisión."), tr("Evidence boundary", "Límite de evidencia"): tr("Not a warning system or deterministic prediction service.", "No es sistema de alerta ni servicio de predicción determinista.")},
    ]
    st.markdown(_html_table(cycle_rows, headers=list(cycle_rows[0].keys())), unsafe_allow_html=True)

    _section_intro(
        "Publication Components",
        "Componentes de publicación",
        "These rows connect visible sections with the artifacts and logic that support them.",
        "Estas filas conectan las secciones visibles con los artefactos y la lógica que las soportan.",
    )
    rows = [
        {tr("Section", "Sección"): tr("Executive Overview", "Resumen Ejecutivo"), tr("Primary support", "Soporte principal"): tr("Publication snapshot overview, hero plots, hero reports", "Resumen del snapshot de publicación, plots principales, reportes principales")},
        {tr("Section", "Sección"): tr("Mexico Executive Map", "Mapa Ejecutivo de México"), tr("Primary support", "Soporte principal"): tr("SQLite aggregation, executive map payload, historical and recent event layers", "Agregación en SQLite, payload del mapa ejecutivo, capas de eventos históricos y recientes")},
        {tr("Section", "Sección"): tr("Regional Risk View", "Vista Regional de Riesgo"), tr("Primary support", "Soporte principal"): tr("Region features, publication snapshot regional concentration, governed regional labels", "Features regionales, concentración regional del snapshot de publicación, etiquetas regionales gobernadas")},
        {tr("Section", "Sección"): tr("Model Evaluation", "Evaluación del Modelo"), tr("Primary support", "Soporte principal"): tr("Evaluation payload when persisted, otherwise explicit fallback policy", "Payload de evaluación cuando existe, de otro modo política explícita de fallback")},
        {tr("Section", "Sección"): tr("Future Projection", "Proyección futura"), tr("Primary support", "Soporte principal"): tr("Roadmap-grade engineering next steps for AI, ML, on-premise, and cloud expansion", "Siguientes pasos de ingeniería tipo roadmap para expansión con IA, ML, on-premise y cloud")},
    ]
    st.dataframe(rows, width="stretch", hide_index=True)

    _section_intro("Plot Inventory", "Inventario de plots", "Persisted visuals that support the public reading.", "Visuales persistidos que apoyan la lectura pública.")
    st.markdown(_html_table(plot_rows, headers=list(plot_rows[0].keys())), unsafe_allow_html=True)

    _section_intro("Report Inventory", "Inventario de reportes", "Persisted report narratives used to reinforce publication traceability.", "Narrativas persistidas de reportes usadas para reforzar la trazabilidad de publicación.")
    st.markdown(_html_table(report_rows, headers=list(report_rows[0].keys())), unsafe_allow_html=True)

    _section_intro(
        "Persisted Data Support",
        "Soporte persistido de datos",
        "This summary replaces raw code-like payloads with compact descriptive reading aids.",
        "Este resumen reemplaza payloads tipo código por ayudas descriptivas compactas.",
    )
    support_rows = [
        {tr("Component", "Componente"): tr("Curated event overview", "Resumen de eventos curados"), tr("Current state", "Estado actual"): _safe_metric_value((snapshot.get("overview") or {}).get("total_events")), tr("Reading", "Lectura"): tr("Historical coverage used by overview and map sections", "Cobertura histórica usada por las secciones de resumen y mapa")},
        {tr("Component", "Componente"): tr("Latest feature generation", "Última generación de features"), tr("Current state", "Estado actual"): (summary.get("latest_feature_generation") or {}).get("status") or tr("Not published", "No publicado"), tr("Reading", "Lectura"): tr("Latest persisted feature-generation metadata", "Metadatos persistidos más recientes de generación de features")},
        {tr("Component", "Componente"): tr("Latest model run", "Última ejecución del modelo"), tr("Current state", "Estado actual"): (summary.get("latest_model_run") or {}).get("status") or tr("Not published", "No publicado"), tr("Reading", "Lectura"): tr("Latest persisted model-run metadata", "Metadatos persistidos más recientes de ejecución del modelo")},
        {tr("Component", "Componente"): tr("Latest evaluation artifact", "Último artefacto de evaluación"), tr("Current state", "Estado actual"): (summary.get("latest_evaluation") or {}).get("evaluation_id") or tr("Publication-limited but available", "Disponibles con límite de publicación"), tr("Reading", "Lectura"): tr("Evaluation remains explicit and bounded when artifacts are absent", "La evaluación permanece explícita y acotada cuando faltan artefactos")},
    ]
    st.markdown(_html_table(support_rows, headers=list(support_rows[0].keys())), unsafe_allow_html=True)





def render_api_integration() -> None:
    st.subheader(tr("API & Integration Surface", "API y Superficie de Integración"))
    st.caption(tr("This section presents the API as a bounded local integration surface for structured outputs.", "Esta sección presenta la API como una superficie local de integración acotada para salidas estructuradas."))
    st.markdown(f'<div class="hero-box"><b>{tr("Why this surface exists", "Por qué existe esta superficie")}</b><br><br>{tr("The API exposes the same bounded publication state through read-oriented endpoints so the prototype remains inspectable, automatable, and integration-friendly without behaving like a production backend.", "La API expone el mismo estado de publicación acotado mediante endpoints orientados a lectura para que el prototipo siga siendo inspeccionable, automatizable y amigable para integración sin comportarse como un backend de producción.")}</div>', unsafe_allow_html=True)
    chips = ["/health", "/summary/latest", "/regions/{region_code}/latest", "/evaluation/latest"]
    st.markdown(''.join([f'<span class="endpoint-chip">{c}</span>' for c in chips]), unsafe_allow_html=True)
    cols = st.columns(4)
    with cols[0]: _present_metric(tr("Mode", "Modo"), tr("Read-oriented", "Orientado a lectura"))
    with cols[1]: _present_metric(tr("Network posture", "Postura de red"), tr("Local-first", "Local-first"))
    with cols[2]: _present_metric(tr("Scope", "Alcance"), tr("Bounded", "Acotado"))
    with cols[3]: _present_metric(tr("Usage", "Uso"), tr("Controlled inspection", "Inspección controlada"))
    st.info(tr("The API is read-oriented, bounded, and intended for local or controlled-network inspection. For contract details, see docs/api_contract.md.", "La API es orientada a lectura, acotada y pensada para inspección local o en red controlada. Para detalles del contrato, consulta docs/api_contract.md."))
def render_future_projection() -> None:
    st.subheader(tr("Future Projection", "Proyección futura"))
    st.caption(tr("This section describes the next engineering stages that could expand the prototype toward broader ML/AI integration without breaking its current local-first and governed design.", "Esta sección describe las siguientes etapas de ingeniería que podrían expandir el prototipo hacia una integración más amplia de ML/IA sin romper su diseño actual local-first y gobernado."))

    st.markdown(f'<div class="narrative-box"><b>{tr("Strategic expansion posture", "Postura estratégica de expansión")}</b><br><br>{tr("The current prototype is intentionally bounded. Its future value comes from disciplined expansion: more capable ML/AI stages, richer geospatial authority, and optional on-premise or cloud integration that preserves traceability, idempotence, and architectural coherence.", "El prototipo actual es intencionalmente acotado. Su valor futuro proviene de una expansión disciplinada: etapas más capaces de ML/IA, autoridad geoespacial más rica e integración opcional on-premise o cloud que preserve trazabilidad, idempotencia y coherencia arquitectónica.")}</div>', unsafe_allow_html=True)

    top = st.columns(2)
    with top[0]:
        st.markdown(f'<div class="hero-box"><b>{tr("Why this matters next", "Por qué importa a continuación")}</b><br><br>{tr("The current repository already demonstrates bounded value. The next phase should not chase novelty first; it should extend the same governance, traceability, and architectural discipline into richer AI/ML and geospatial capability.", "El repositorio actual ya demuestra valor acotado. La siguiente fase no debe perseguir novedad primero; debe extender la misma gobernanza, trazabilidad y disciplina arquitectónica hacia capacidades más ricas de IA/ML y geoespacialidad.")}</div>', unsafe_allow_html=True)
    with top[1]:
        st.markdown(f'<div class="hero-box"><b>{tr("Integration posture", "Postura de integración")}</b><br><br>{tr("Future integration should remain optional and layered: on-premise services for low-latency local experimentation, cloud augmentation for heavier workloads, and canonical geometry only when formally ingested and validated.", "La integración futura debe permanecer opcional y por capas: servicios on-premise para experimentación local de baja latencia, expansión cloud para cargas más pesadas y geometría canónica solo cuando sea ingerida y validada formalmente.")}</div>', unsafe_allow_html=True)

    cards = st.columns(2)
    for idx, (en_title, en_body, es_title, es_body) in enumerate(FUTURE_STEPS):
        with cards[idx % 2]:
            st.markdown(f'<div class="hero-box"><b>{tr(en_title, es_title)}</b><br><br>{tr(en_body, es_body)}</div>', unsafe_allow_html=True)

    _section_intro(
        "Roadmap Summary",
        "Resumen del roadmap",
        "This table condenses the future tracks into publication-safe next steps without overstating implementation maturity.",
        "Esta tabla condensa las líneas futuras en siguientes pasos aptos para publicación sin sobredimensionar la madurez de implementación.",
    )
    roadmap_rows = [{
        tr("Track", "Línea"): tr(en_title, es_title),
        tr("Current status", "Estado actual"): tr("Pending next phase", "Pendiente para siguiente fase"),
        tr("Engineering value", "Valor de ingeniería"): tr("Extends prototype maturity without breaking current bounded scope.", "Extiende la madurez del prototipo sin romper el alcance acotado actual."),
    } for en_title, en_body, es_title, es_body in FUTURE_STEPS]
    st.dataframe(roadmap_rows, width="stretch", hide_index=True)


def main() -> None:
    render_header()
    bundle = fetch_publication_bundle()
    map_style, color_key = render_sidebar(bundle)
    section = st.session_state.get("section", "overview")
    if section == "overview":
        render_overview()
    elif section == "mexico_map":
        render_mexico_map(map_style, color_key)
    elif section == "regional":
        render_regional()
    elif section == "evaluation":
        render_evaluation()
    elif section == "methodology":
        render_methodology()
    elif section == "api":
        render_api_integration()
    else:
        render_future_projection()

if __name__ == "__main__":
    main()
