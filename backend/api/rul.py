from fastapi import APIRouter, HTTPException

from schemas.health import RULEstimate, DegradationState
from telemetry.streaming import engine

router = APIRouter(prefix="/rul", tags=["rul"])


@router.get("", response_model=RULEstimate)
def get_rul():
    latest = engine.latest()
    if latest is None or latest.rul is None:
        raise HTTPException(status_code=404, detail="No RUL estimate yet — POST /api/simulation/start first.")
    return latest.rul


@router.get("/degradation", response_model=DegradationState)
def get_degradation():
    latest = engine.latest()
    if latest is None or latest.degradation is None:
        raise HTTPException(status_code=404, detail="No degradation state yet — POST /api/simulation/start first.")
    return latest.degradation
