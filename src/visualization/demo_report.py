from __future__ import annotations

from pathlib import Path
import json

from src.common.clock import utc_now_iso


def write_demo_evidence_md(payload: dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plots = payload.get("plots", [])
    plot_lines = "\n".join(f"- {p}" for p in plots)

    text = f"""# Demo Evidence

- generated_at_utc: {utc_now_iso()}
- source_id: {payload.get('source_id', 'n/a')}
- ingest_batch_id: {payload.get('ingest_batch_id', 'n/a')}
- feature_set_version: {payload.get('feature_set_version', 'n/a')}
- raw_files_count: {payload.get('raw_files_count', 'n/a')}
- curated_events_count: {payload.get('curated_events_count', 'n/a')}
- feature_generation_id: {payload.get('feature_generation_id', 'n/a')}
- model_artifact: {payload.get('model_artifact', 'n/a')}
- metrics_path: {payload.get('metrics_path', 'n/a')}

## Plots
{plot_lines}

## Scope note
This prototype estimates probabilistic regional risk from historical data patterns.
It is not a deterministic earthquake prediction system and not an official warning system.

## Observed limitations
- regional grouping may be simplified
- current risk map is a prototype regional surface
- target definition is baseline-oriented and must be interpreted as a controlled prototype assumption
"""
    output_path.write_text(text, encoding="utf-8")
    return output_path


def write_demo_evidence_json(payload: dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path
