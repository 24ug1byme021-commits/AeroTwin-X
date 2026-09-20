from fastapi import APIRouter, HTTPException

from schemas.health import EngineStateSnapshot
from schemas.prediction import SystemStatus
from telemetry.streaming import engine

router = APIRouter(tags=["system"])


@router.get("/health")
def liveness_check():
    """Plain liveness probe — distinct from /api/health/status, which is
    the engine's own AI-derived health assessment."""
    return {"status": "ok", "service": "AeroTwin-X backend"}


@router.get("/api/system/status", response_model=SystemStatus)
def get_system_status():
    return engine.status()


@router.get("/api/engine/state", response_model=EngineStateSnapshot)
def get_engine_state():
    latest = engine.latest()
    if latest is None:
        raise HTTPException(status_code=404, detail="No engine state yet — POST /api/simulation/start first.")
    return EngineStateSnapshot(
        timestamp=latest.telemetry.timestamp,
        telemetry_source=latest.telemetry.source.value,
        residuals=latest.residuals,
        sensor_fault=latest.sensor_fault,
        health=latest.health,
        degradation=latest.degradation,
        rul=latest.rul,
    )
