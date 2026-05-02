from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .repository import (
    get_executive_mexico_map,
    get_latest_evaluation,
    get_latest_region,
    get_latest_summary,
)
from .schemas import EvaluationLatestResponse, HealthResponse, RegionLatestResponse, SummaryResponse


app = FastAPI(title="Probabilistic Seismic Risk Prototype API")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/summary/latest", response_model=SummaryResponse)
def summary_latest() -> SummaryResponse:
    return SummaryResponse(**get_latest_summary())


@app.get("/regions/{region_code}/latest", response_model=RegionLatestResponse)
def region_latest(region_code: str) -> RegionLatestResponse:
    payload = get_latest_region(region_code)
    if payload is None:
        raise HTTPException(status_code=404, detail=f"Region not found: {region_code}")
    return RegionLatestResponse(**payload)


@app.get("/evaluation/latest", response_model=EvaluationLatestResponse)
def evaluation_latest() -> EvaluationLatestResponse:
    return EvaluationLatestResponse(**get_latest_evaluation())


@app.get("/executive/mexico-map")
def executive_mexico_map() -> dict:
    return get_executive_mexico_map()
