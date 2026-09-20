from fastapi import APIRouter, HTTPException

from schemas.health import ResidualFrame
from telemetry.streaming import engine

router = APIRouter(prefix="/physics", tags=["physics"])


@router.get("/current", response_model=ResidualFrame)
def get_current_residuals():
    latest = engine.latest()
    if latest is None or latest.residuals is None:
        raise HTTPException(status_code=404, detail="No residuals yet — POST /api/simulation/start first.")
    return latest.residuals
